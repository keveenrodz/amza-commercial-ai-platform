# 014 Admin Governance & Access Control

## Propósito

Cuarto paso del rediseño (specs 011-013, ver `PROJECT_STATE.md` sección "Next Step"). Hasta hoy,
crear un `InternalUser` (Advisor o Administrator) solo es posible vía `scripts/create_user.py` —
un script de operaciones, no algo que un administrador pueda hacer desde la plataforma. Este spec
construye eso: una pantalla real en `/admin` (spec 011 la dejó como placeholder "Próximamente"),
las reglas de gobernanza ya acordadas antes de escribir esta spec (ver `PROJECT_STATE.md`), y el
**primer uso real** de `require_role()` — construido en spec 008, nunca conectado a un endpoint.

**Reglas de negocio, decididas antes de este spec (no se re-discuten aquí):**

1. Existe un administrador **principal** — el primer `InternalUser` con rol Administrator que se
   crea en una organización.
2. Cualquier administrador (principal o no) puede crear administradores o asesores nuevos.
3. **Solo** el administrador principal puede desactivar a otro administrador.
4. Nadie puede desactivarse a sí mismo — ni siquiera el principal.
5. Desactivar a un asesor no tiene esa restricción — cualquier administrador activo puede hacerlo.

**Explícitamente fuera de alcance:**

- Transferir la insignia de "principal" a otro administrador — caso raro y de alto riesgo (¿qué
  pasa si la cuenta de Google del principal se pierde?); se resuelve manualmente vía script (ver
  sección 6), no con una pantalla — decisión ya tomada antes de este spec, no se reabre aquí.
- Cambiar el rol de un `InternalUser` ya creado (de Advisor a Administrator o viceversa) — el rol
  se fija al crear, igual que ya hacía `create_user.py`; no se pidió una función de "promover".
- Cualquier permiso más fino sobre `opportunities.py` (spec 013 dejó anotado que "cualquiera puede
  reasignar" no era una laguna suya, sino de este spec) — **tampoco se resuelve aquí**: este spec
  cubre gobernanza de *usuarios*, no permisos por rol sobre *oportunidades*. Se anota como
  candidato futuro, ver "Próximo paso".

---

## 1. Migración — `0005_add_admin_governance`

```python
def upgrade() -> None:
    op.add_column(
        "internal_users",
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_internal_users_primary_admin",
        "internal_users",
        ["organization_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1"),
    )

    # Backfill: si ya existe algún Administrator (ej. el sembrado manualmente en spec 008 para
    # validar OAuth), el más antiguo por organización se marca principal. No-op si no hay ninguno.
    op.execute(
        """
        UPDATE internal_users
        SET is_primary = 1
        WHERE id IN (
            SELECT id FROM internal_users iu
            WHERE role = 'administrator'
            AND created_at = (
                SELECT MIN(created_at) FROM internal_users
                WHERE organization_id = iu.organization_id AND role = 'administrator'
            )
        )
        """
    )
```

El índice único parcial (`sqlite_where`, soportado por SQLite ≥ 3.8) es la red de seguridad real
contra la condición de carrera de la sección 2 — dos solicitudes de creación concurrentes no
pueden dejar dos administradores principales en la misma organización, la base de datos lo
rechaza aunque el caso de uso no alcance a comprobarlo a tiempo. Aceptado como suficiente para
MVP: la probabilidad de dos altas de administrador *simultáneas* en esta plataforma es
prácticamente nula.

---

## 2. `InternalUser` — campo `is_primary`

`core/entities/internal_user.py` — un campo nuevo, sin métodos de comportamiento (se asigna una
sola vez, al crear; nunca se "activa" después):

```python
is_primary: bool = False
```

`core/exceptions/domain.py` — tres excepciones nuevas:

```python
class InternalUserEmailAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"An internal user with email {email!r} already exists")


class CannotRemoveSelfError(DomainError):
    def __init__(self, user_id: InternalUserId) -> None:
        super().__init__(f"InternalUser {user_id} cannot deactivate itself")


class OnlyPrimaryAdminCanDeactivateAdminsError(DomainError):
    def __init__(self, target_id: InternalUserId) -> None:
        super().__init__(f"Only the primary administrator can deactivate {target_id}")
```

`app/exceptions.py` — las tres van a `_UNPROCESSABLE_ERRORS` (422), **no** a `_FORBIDDEN_ERRORS`
(403), aunque las dos últimas son en el fondo reglas de permiso. Mismo criterio ya establecido por
`OpportunityNotAssignedToAdvisorError` (spec 010) — también una regla de permiso sobre una acción
concreta, y también vive en 422: el handler de `_FORBIDDEN_ERRORS` siempre devuelve el mensaje
genérico `"Access denied"`, perdiendo el motivo específico (`str(exc)`); el de
`_UNPROCESSABLE_ERRORS` sí lo conserva. Preferible que un administrador vea "solo el administrador
principal puede desactivar a otro administrador" en vez de un "Access denied" sin contexto.

---

## 3. `InternalUserRepository` — dos métodos nuevos

`core/interfaces/repositories.py`:

```python
async def list_by_organization(self, organization_id: OrganizationId) -> list[InternalUser]: ...

async def get_primary_administrator(
    self,
    organization_id: OrganizationId,
) -> InternalUser | None: ...
```

`list_by_organization` devuelve **todos** los `InternalUser` (cualquier rol, cualquier estado) —
a diferencia de `list_advisors_by_organization` (spec 008, solo Advisor+activo, para el selector
de reasignación de spec 013), esta es para la pantalla de administración, donde sí hace falta ver
también a los administradores y a los desactivados.

`modules/users/repositories/internal_user.py`:

```python
async def list_by_organization(self, organization_id: OrganizationId) -> list[InternalUser]:
    result = await self._session.execute(
        select(InternalUserModel)
        .where(InternalUserModel.organization_id == organization_id.value)
        .order_by(InternalUserModel.full_name.asc())
    )
    return [_to_entity(m) for m in result.scalars().all()]


async def get_primary_administrator(
    self,
    organization_id: OrganizationId,
) -> InternalUser | None:
    result = await self._session.execute(
        select(InternalUserModel).where(
            InternalUserModel.organization_id == organization_id.value,
            InternalUserModel.is_primary == True,  # noqa: E712 -- comparación SQL, no Python
        )
    )
    model = result.scalar_one_or_none()
    return _to_entity(model) if model else None
```

(`_to_entity`/`_from_entity` ganan el campo `is_primary` — sin sorpresas, mismo patrón que
cualquier campo nuevo en este repositorio.)

---

## 4. Casos de uso

`app/use_cases/create_internal_user.py`:

```python
class CreateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        organization_slug: str,
        full_name: str,
        email: str,
        role: InternalUserRole,
    ) -> InternalUser:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            if await uow.internal_users.get_by_email(email) is not None:
                raise InternalUserEmailAlreadyExistsError(email)

            is_primary = False
            if role == InternalUserRole.ADMINISTRATOR:
                existing_primary = await uow.internal_users.get_primary_administrator(
                    organization.id,
                )
                is_primary = existing_primary is None

            now = datetime.now(tz=UTC)
            user = InternalUser(
                id=InternalUserId.generate(),
                organization_id=organization.id,
                full_name=full_name,
                email=email,
                role=role,
                status=InternalUserStatus.ACTIVE,
                is_primary=is_primary,
                created_at=now,
                updated_at=now,
            )
            await uow.internal_users.save(user)
            await uow.commit()
        return user
```

`app/use_cases/deactivate_internal_user.py`:

```python
class DeactivateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, actor_id: InternalUserId, target_id: InternalUserId) -> InternalUser:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            target = await uow.internal_users.get_by_id(target_id)
            if target is None:
                raise InternalUserNotFoundError(target_id)

            if target.id == actor_id:
                raise CannotRemoveSelfError(actor_id)

            if target.role == InternalUserRole.ADMINISTRATOR:
                actor = await uow.internal_users.get_by_id(actor_id)
                assert actor is not None  # invariante: actor viene de get_current_user, ya autenticado
                if not actor.is_primary:
                    raise OnlyPrimaryAdminCanDeactivateAdminsError(target_id)

            target.status = InternalUserStatus.INACTIVE
            target.updated_at = datetime.now(tz=UTC)
            await uow.internal_users.save(target)
            await uow.commit()
        return target
```

`app/use_cases/activate_internal_user.py` — mismo patrón, sin ninguna de las dos comprobaciones
(reactivar a alguien no tiene el riesgo que la regla 3 busca evitar — no hace que nadie pierda
acceso):

```python
class ActivateInternalUserUseCase:
    async def execute(self, target_id: InternalUserId) -> InternalUser:
        # carga, target.status = InternalUserStatus.ACTIVE, save, commit -- sin más chequeos.
        ...
```

`app/use_cases/list_internal_users.py` — resuelve la organización por slug, delega en
`list_by_organization`. Mismo patrón que `ListOpenOpportunitiesUseCase`.

---

## 5. API

`app/api/dto/internal_user.py` (nuevo):

```python
class InternalUserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    status: str
    is_primary: bool

    @classmethod
    def from_domain(cls, user: InternalUser) -> InternalUserResponse:
        return cls(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            is_primary=user.is_primary,
        )


class CreateInternalUserRequest(BaseModel):
    full_name: str
    email: str
    role: Literal["advisor", "administrator"]
```

`role` como `Literal`, no `str` — un valor inválido lo rechaza Pydantic con 422 directo, en vez de
que `InternalUserRole(role)` lance un `ValueError` sin capturar dentro del caso de uso (ningún DTO
anterior tenía este problema porque ninguno recibía un rol desde el body; este es el primero).

`app/api/routers/internal_users.py` (nuevo), montado en
`/organizations/{organization_slug}/users`, protegido con `require_role` — **primer uso real**
de esa dependencia, construida en spec 008 y nunca conectada hasta ahora:

```python
router = APIRouter(
    prefix="/organizations/{organization_slug}/users",
    tags=["internal-users"],
    dependencies=[Depends(require_role(InternalUserRole.ADMINISTRATOR))],
)


@router.get("")
async def list_internal_users(
    organization_slug: str,
    use_case: ListInternalUsersUseCase = Depends(get_list_internal_users_use_case),
) -> list[InternalUserResponse]:
    users = await use_case.execute(organization_slug)
    return [InternalUserResponse.from_domain(u) for u in users]


@router.post("", status_code=201)
async def create_internal_user(
    organization_slug: str,
    body: CreateInternalUserRequest,
    use_case: CreateInternalUserUseCase = Depends(get_create_internal_user_use_case),
) -> InternalUserResponse:
    user = await use_case.execute(
        organization_slug, body.full_name, body.email, InternalUserRole(body.role),
    )
    return InternalUserResponse.from_domain(user)


@router.post("/{user_id}/deactivate")
async def deactivate_internal_user(
    organization_slug: str,
    user_id: str,
    current_user: InternalUser = Depends(require_role(InternalUserRole.ADMINISTRATOR)),
    use_case: DeactivateInternalUserUseCase = Depends(get_deactivate_internal_user_use_case),
) -> InternalUserResponse:
    user = await use_case.execute(current_user.id, InternalUserId.from_string(user_id))
    return InternalUserResponse.from_domain(user)


@router.post("/{user_id}/activate")
async def activate_internal_user(
    organization_slug: str,
    user_id: str,
    use_case: ActivateInternalUserUseCase = Depends(get_activate_internal_user_use_case),
) -> InternalUserResponse:
    user = await use_case.execute(InternalUserId.from_string(user_id))
    return InternalUserResponse.from_domain(user)
```

**Detalle importante, distinto de todos los endpoints anteriores de este proyecto:** el actor de
`deactivate_internal_user` viene de `current_user.id` (la sesión autenticada real), **nunca** del
body — a diferencia de `advisor_id` en `assign-advisor`/`messages` (spec 009/010), que sí viaja en
el body porque cualquier asesor podía actuar como cualquier asesor sin implicación de privilegios.
Aquí sí hay una implicación de privilegios (la regla 3 depende de *quién realmente* está haciendo
la llamada) — dejar que el frontend declare `actor_id` en el body permitiría que cualquier
administrador se hiciera pasar por el principal. Por eso el endpoint pide `current_user` dos veces
(una vía el router, otra vía el parámetro) — la del parámetro es la que realmente importa para
`actor_id`, la del router solo gatea que sea Administrator.

`app/api/dto/auth.py` — `CurrentUserResponse` gana `is_primary: bool` (mismo patrón de siempre,
un campo más al `from_domain()`) — el frontend lo necesita para decidir si mostrar habilitado el
botón de desactivar sobre otro administrador, sin adivinar.

---

## 6. `scripts/create_user.py` — deja de duplicar la lógica de creación

El script pasa a llamar al mismo caso de uso que el endpoint nuevo, en vez de construir el
`InternalUser` a mano — evita que la lógica de `is_primary` viva en dos lugares que puedan
desincronizarse (y el script sigue siendo el único camino para crear el **primer** usuario de una
organización nueva, antes de que exista ningún administrador que pueda usar la pantalla):

```python
async def create_user(org_slug: str, email: str, full_name: str, role: str) -> None:
    use_case = CreateInternalUserUseCase(session_factory=AsyncSessionFactory)
    user = await use_case.execute(org_slug, full_name, email, InternalUserRole(role))
    print(f"InternalUser creado: {user.full_name} <{user.email}> ({user.role.value})"
          f"{' [principal]' if user.is_primary else ''}")
```

`scripts/reassign_primary_admin.py` (nuevo, pequeño) — la única forma de mover la insignia de
principal a otro administrador, para el caso raro anotado como fuera de alcance en "Propósito":
recibe el email del nuevo principal, comprueba que sea un Administrator activo de la organización,
le pone `is_primary = True` y se lo quita al anterior (una sola transacción, para que el índice
único de la sección 1 nunca vea dos principales a la vez). Deliberadamente sin exponer esto como
endpoint — es una operación rara y de alto riesgo, un script con confirmación manual es
proporcional al riesgo.

---

## 7. Frontend — `/admin` deja de ser un placeholder

`frontend/app/(workspace)/admin/page.tsx` (spec 011 la dejó con el mensaje "Próxima spec" —
reemplazo completo, no una extensión del placeholder):

- Tabla de usuarios (`useInternalUsers()`, nuevo hook): nombre, email, rol, estado, insignia
  "Principal" junto al nombre si `is_primary`.
- Formulario "Agregar usuario" (`useCreateInternalUser()`): nombre, email, rol — sin contraseña,
  mismo criterio que `create_user.py` desde spec 008 (autenticación vía Google OAuth).
- Botón desactivar/activar por fila (`useDeactivateInternalUser()`/`useActivateInternalUser()`),
  deshabilitado en el cliente (con un texto explicando por qué) cuando:
  - la fila es el usuario actual (`user.id === currentUser.id`), o
  - la fila es un Administrator y `!currentUser.is_primary`.

  Esto es solo cortesía de UX — quien de verdad impide la acción es el backend (sección 4); un
  botón deshabilitado que de todos modos fallara en el servidor sería la señal de que el chequeo
  del cliente y el del servidor se desincronizaron, no una segunda capa de seguridad real.

`frontend/types/api.ts` — `CurrentUser` gana `is_primary: boolean`; nuevo `InternalUserSummary`
(mismos campos que `InternalUserResponse`).

`frontend/components/workspace-shell.tsx` (spec 011) — el ítem de navegación "Administración" solo
se renderiza si `currentUser.role === "administrator"`; un asesor nunca lo ve (coherente con que el
backend igual lo bloquearía con 403 — no tiene sentido mostrar un enlace que siempre falla).

---

## 8. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- Backend (`tests/test_admin_governance.py`, nuevo):
  1. Crear el primer Administrator de una organización → `is_primary=True`.
  2. Crear un segundo Administrator → `is_primary=False`.
  3. Crear un Advisor → `is_primary` siempre `False`, sin importar si es el primer `InternalUser`.
  4. Crear con un email ya existente → 422.
  5. Un administrador no-principal intenta desactivar a otro administrador → 422
     (`OnlyPrimaryAdminCanDeactivateAdminsError`, mensaje específico en el body).
  6. El administrador principal desactiva a otro administrador → 200.
  7. Cualquier administrador (principal o no) desactiva a un Advisor → 200.
  8. Cualquier usuario intenta desactivarse a sí mismo (principal incluido) → 422
     (`CannotRemoveSelfError`).
  9. Un Advisor autenticado llama cualquier endpoint de `/users` → 403 (`require_role` en acción
     por primera vez en el proyecto).
  10. Migración: backfill deja exactamente un `is_primary=True` por organización cuando ya existía
      al menos un Administrator antes de aplicarla (validar contra el estado real de desarrollo,
      con el administrador sembrado en spec 008).
- Frontend (`frontend/tests/e2e/`, nuevo archivo o extensión): un administrador ve `/admin`, crea
  un usuario nuevo, lo ve aparecer en la tabla; un asesor no ve el ítem "Administración" en la
  barra lateral y recibe 403 si navega directo a `/admin`.

---

## Próximo paso

Spec 015 — **Contact Channel Tagging**: etiqueta de canal en `Contact` (Telegram/WhatsApp ya
existen como valores de `ChannelType` desde spec 002, spec 012 ya los usa para el chip de la
lista) — el ajuste real es de datos/producto, no de UI, y es prerrequisito directo de spec 016
(WhatsApp Integration).

Permisos por rol sobre `opportunities.py` (quién puede reasignar, quién puede ver "Todas" vs solo
"Mías") quedan anotados como candidato futuro, no resueltos aquí ni en spec 013 — se decide cuando
haga falta, no antes.
