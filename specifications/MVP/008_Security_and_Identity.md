# 008 Security & Identity

## Propósito

Cerrar la laguna más grave encontrada al validar la plataforma con tráfico real: todos los
endpoints de `/organizations/*` están completamente abiertos — cualquiera que descubra la URL
puede leer historiales de conversación con datos de clientes, o reasignar oportunidades. Este spec
introduce autenticación (Google OpenID Connect), autorización por rol, y las piezas de identidad
(`InternalUser`) que hoy no tienen ninguna forma de crearse ni de iniciar sesión.

No incluye frontend — solo los tres endpoints (`/auth/google/login`, `/auth/google/callback`,
`/auth/me`) que el frontend consumirá cuando se construya (spec 009+).

---

## Principio arquitectónico

> Autenticarse con éxito prueba que controlas una dirección de correo. No otorga acceso a la
> plataforma. El acceso solo se concede si ya existe un `InternalUser` activo para ese correo.
>
> *Authentication never creates identities.*

Como no hay restricción de dominio posible (el MVP acepta cualquier cuenta de Google, no solo
`@amza.com` — ver sección 8), esta comprobación es el **único** control de acceso real del
sistema. No hay ninguna capa de defensa adicional del lado de Google — todo depende de que este
chequeo se implemente correctamente y nunca se salte.

---

## 1. Identity — `InternalUser`

La entidad ya existe desde spec 002 y no necesita cambios — ya tiene `email`, `role`
(`InternalUserRole.ADVISOR` / `ADMINISTRATOR`), `status` (`ACTIVE` / `INACTIVE`). Lo que falta es
poder crearla y buscarla por email.

### Corrección a Spec 002 — `core/interfaces/repositories.py`

```python
class InternalUserRepository(Protocol):
    async def get_by_id(self, id: InternalUserId) -> InternalUser | None: ...

    async def get_by_email(self, email: str) -> InternalUser | None: ...

    async def list_advisors_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[InternalUser]: ...

    async def save(self, internal_user: InternalUser) -> None: ...
```

`get_by_email()` es el método central de todo este spec — es lo único que conecta un login exitoso
de Google con una cuenta real de la plataforma. `save()` no existía; lo necesita el bootstrap
(sección 6).

**`InternalUser.email` debe ser único, sin distinguir mayúsculas/minúsculas** —
`Juan@gmail.com` y `juan@gmail.com` son la misma persona. **Corrección de último momento:** la
migración `0001_initial_schema.py` ya declara `sa.UniqueConstraint('email')` — la restricción de
unicidad a nivel BD ya existe desde spec 001, no hace falta ninguna migración nueva. Lo que falta
es solo la parte de mayúsculas/minúsculas: `UniqueConstraint` en SQLite compara los bytes
exactos, así que `Juan@gmail.com` y `juan@gmail.com` hoy pasarían como dos filas distintas. La
comparación se normaliza a minúsculas tanto al guardar (`save()`) como al buscar
(`get_by_email()`) — con eso, la restricción ya existente se comporta como case-insensitive en la
práctica, porque el código nunca escribe ni compara nada que no esté ya en minúsculas. La
unicidad es **global**, no por organización: el login busca por email sin conocer todavía a qué
organización pertenece la persona, así que dos organizaciones no pueden compartir el mismo email
de `InternalUser`.

### Corrección a Spec 004 — `modules/users/repositories/internal_user.py`

Agrega ambos métodos con el mismo patrón `_to_entity`/`_from_entity` que ya usa el resto de
repositorios (`save()` vía `session.merge()`, igual que `AgentRepository`). `get_by_email()`
normaliza el argumento a minúsculas antes de comparar; `save()` normaliza `entity.email` antes de
persistir.

---

## 2. Authentication — `AuthProvider`

### Nuevo — `core/interfaces/auth.py`

Protocol nuevo, separado de `core/interfaces/providers.py` — es un concern distinto (identidad,
no infraestructura de IA/canal). Se justifica como `Protocol` (no clase concreta) bajo la regla de
Engineering Principles post-spec-006: ya hay **dos implementaciones comprometidas**, no
especulativas — Google ahora, Microsoft en una versión posterior (sección "Future Evolution").

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AuthenticatedIdentity:
    email: str
    full_name: str
    provider: Literal["google"]


class AuthProvider(Protocol):
    def get_authorization_url(self, state: str, redirect_uri: str) -> str: ...

    async def exchange_code(self, code: str, redirect_uri: str) -> AuthenticatedIdentity: ...
```

`AuthenticatedIdentity` no incluye el `sub` del proveedor — el email es el identificador de
autenticación en este dominio (ver sección 8), y `AuthProvider` solo devuelve lo que el dominio
necesita. `provider` sí se incluye, aunque el dominio no lo use para nada hoy — es puramente para
auditoría (sección 5: `auth.login_success` registra con qué proveedor entró cada persona). El día
que exista `MicrosoftOAuthProvider`, ese campo se vuelve `Literal["google", "microsoft"]`.

`exchange_code()` valida internamente todas las invariantes del protocolo OIDC (firma del
`id_token`, `issuer`, `audience`, expiración, y **`email_verified: true`**) y lanza si alguna
falla — esto no es una decisión de negocio, es la integridad mínima de la aserción de identidad.
Un email no verificado no es una identidad, es una afirmación sin respaldo.

### Nuevo — `infrastructure/auth/google.py`

`GoogleOAuthProvider` implementa `AuthProvider` con `httpx` (ya es dependencia del proyecto) +
`PyJWT` — no se agrega `authlib`. Verificar el `id_token` de Google es exactamente el mismo
problema que verificar nuestro propio JWT (firma contra un JWKS, `issuer`, `audience`,
expiración), y `PyJWT.PyJWKClient` ya lo resuelve sin una dependencia adicional. Flujo
*Authorization Code* — el backend es un cliente confidencial (tiene `client_secret`), así que no
hace falta PKCE: esa protección existe para clientes públicos que no pueden guardar un secreto
(SPAs, apps móviles), y el frontend nunca ve el `client_secret` ni el código de autorización
(sección 9).

---

## 3. Authorization — roles

`InternalUserRole.ADVISOR` / `ADMINISTRATOR` ya existen (spec 002). Se agrega la dependencia que
los hace cumplir:

```python
def require_role(*roles: InternalUserRole) -> Callable[..., InternalUser]:
    def dependency(user: InternalUser = Depends(get_current_user)) -> InternalUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency
```

Nota honesta: hoy los 4 endpoints de `/organizations/*` (listar, historial, asignar, devolver a
IA) no tienen ninguna razón real para diferenciar Advisor de Administrator — ambos roles pueden
hacer las cuatro cosas. `require_role()` se construye ahora porque es casi gratis y claramente
va a hacer falta (el día que exista un endpoint de gestión de usuarios, ese sí será
`ADMINISTRATOR`-only) — pero no se inventa una restricción falsa hoy solo para "usarlo".

---

## 4. Session — JWT

`PyJWT`, no `python-jose` (historial de CVEs de verificación de firma en `jose`). Token de acceso
único, sin refresh token — **24 horas de vida**, suficiente para no reautenticar a un asesor
durante su jornada. Claims: `sub` (InternalUserId), `exp`. Deliberadamente **no** se incluyen
`role` ni `organization_id` como claims de confianza ciega — ver corrección abajo.

**Corrección respecto a la primera versión de este spec:** se planteaba que `get_current_user()`
decodificara el JWT y confiara en sus claims sin volver a la BD, por rendimiento. Se descarta: el
costo de un `get_by_id()` es insignificante a esta escala, y evitarlo abre una ventana real de
hasta 24h donde un `InternalUser` desactivado (o con el rol recién cambiado) sigue actuando con
privilegios viejos. `get_current_user()` sí consulta la BD en cada request:

```python
async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> InternalUser:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(access_token, settings.jwt_secret)
    user_id = InternalUserId.from_string(payload["sub"])

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        user = await uow.internal_users.get_by_id(user_id)

    if user is None or user.status != InternalUserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Session no longer valid")
    return user
```

`Cookie(default=None)`, no `Authorization: Bearer` — el JWT vive en la cookie `HttpOnly` que fija
`/auth/google/callback` (sección 7), consistente con la decisión de que el frontend nunca toca el
token directamente.

El JWT sigue siendo stateless (no hay lista de revocación en servidor, no hay refresh token) — lo
único que cambia es que "stateless" se refiere a la sesión, no a la vigencia del `InternalUser`.
Esto también resuelve gratis un caso que la primera versión no cubría: un cambio de rol a mitad de
sesión también se aplica de inmediato, no solo la desactivación.

`app/security.py` gana `get_current_user()` y `require_role()` de la sección 3.

---

## 5. Caso de uso — `AuthenticateUseCase`

Genérico sobre `AuthProvider` — la misma clase sirve para Google y, más adelante, Microsoft; el
router selecciona qué `AuthProvider` inyectar según la ruta (`/auth/google/callback` vs un futuro
`/auth/microsoft/callback`), el caso de uso no sabe ni le importa cuál es.

```python
class AuthenticateUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        auth_provider: AuthProvider,
        jwt_secret: str,
        jwt_ttl_hours: int,
    ) -> None:
        self._session_factory = session_factory
        self._auth_provider = auth_provider
        self._jwt_secret = jwt_secret
        self._jwt_ttl_hours = jwt_ttl_hours

    async def execute(self, code: str, redirect_uri: str) -> str:
        identity = await self._auth_provider.exchange_code(code, redirect_uri)

        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            user = await uow.internal_users.get_by_email(identity.email)

        if user is None or user.status != InternalUserStatus.ACTIVE:
            # Ver Principio Arquitectónico -- este es el único control de acceso real.
            # Log de auditoría, no un simple warning: es un intento de acceso, no un error técnico.
            logger.warning("auth.access_denied", email=identity.email, provider=identity.provider)
            raise AccessDeniedError(identity.email)

        # Auditoría simétrica al caso de rechazo -- un login exitoso también es un evento de
        # seguridad, no solo un dato técnico.
        logger.info(
            "auth.login_success",
            internal_user_id=str(user.id),
            email=user.email,
            provider=identity.provider,
            organization_id=str(user.organization_id),
        )

        return create_access_token(user, self._jwt_secret, self._jwt_ttl_hours)
```

### Corrección a Spec 002 — `core/exceptions/domain.py`

Nueva excepción, distinta de `InternalUserNotFoundError` (esa es para lookup por ID dentro de un
flujo ya autenticado; esta es específicamente el resultado de un intento de login sin cuenta
correspondiente — merece su propio tipo para no mezclar los dos logs):

```python
class AccessDeniedError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"No active InternalUser found for email {email!r}")
        self.email = email
```

`app/exceptions.py` la mapea a 403, no 404 — no queremos confirmar ni negar si el email existe en
otro estado (403 genérico es más seguro que "404 no encontrado" vs "403 inactivo").

---

## 6. Bootstrap — `backend/scripts/create_user.py`

Genérico, no específico de administrador — `InternalUserRole` no distingue nada a nivel técnico,
solo es un valor:

```bash
python scripts/create_user.py --org amza-empaques --email juan@gmail.com --name "Juan Pérez" --role advisor
```

Crea el `InternalUser` con `status=ACTIVE`. Sin contraseña que gestionar — la próxima vez que Juan
se autentique con esa cuenta de Google, el sistema ya lo reconoce. Mismo patrón que
`seed_dev_data.py`: tooling de desarrollo/ops, no código de producto.

---

## 7. Endpoints

`app/api/routers/auth.py`:

- `GET /auth/google/login` — construye la URL de autorización de Google (`state` aleatorio para
  CSRF, registrado server-side con expiración corta) y redirige.
- `GET /auth/google/callback?code=...&state=...` — valida `state` **y lo consume**: se borra del
  registro server-side inmediatamente después de validarlo, antes de intercambiar el código con
  Google. Un `state` nunca es reutilizable, ni siquiera si alguien intenta repetir la misma
  callback URL. Llama a `AuthenticateUseCase.execute()`, y en éxito responde con
  `Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax`. **Decisión tomada, no queda
  abierta**: cookie `HttpOnly`, no JSON body — el frontend es Next.js, y así el JWT nunca es
  accesible desde JavaScript (reduce significativamente el riesgo de robo vía XSS). Esto implica
  que routers protegidos deberán leer el JWT de la cookie, no del header `Authorization` — y que
  hará falta protección CSRF en escritura (`POST`/asignaciones) más adelante, ya que las cookies
  se envían automáticamente en cualquier request al dominio. Anotado, no bloqueante para 008 (hoy
  no hay formularios de terceros que puedan explotarlo).

  **Nota de desarrollo:** `Secure` implica HTTPS — en local (`http://localhost:8000` o
  `http://127.0.0.1:8000`) el navegador simplemente descarta la cookie, no lanza ningún error
  visible. `Secure` se controla vía `settings.debug` (deshabilitado solo en desarrollo local,
  obligatorio en cualquier despliegue real) para que esto no se confunda con "el login no
  funciona" cuando en realidad la cookie nunca se guardó.
- `GET /auth/me` — protegido por `get_current_user()`, devuelve el `InternalUser` autenticado.

Almacén de `state` (login) — en memoria, de un solo proceso, con expiración corta (ej. 5 minutos).
Coherente con el resto del despliegue actual (un solo proceso FastAPI, sin Redis — ver
`000_Technology_Stack.md`). Limitación conocida si algún día hay más de un proceso/réplica
corriendo el backend: un `state` emitido por un proceso no sería válido en otro. Se revisita
cuando exista despliegue multi-proceso, no antes. Es un detalle de infraestructura: podrá migrarse
a Redis u otro almacenamiento compartido el día que haga falta, sin modificar el contrato de
`AuthProvider` ni de `AuthenticateUseCase` — ninguno de los dos sabe cómo se guarda el `state`.

---

## 8. Corrección a Spec 007 — endpoints protegidos

`/organizations/*` (spec 007) gana `Depends(get_current_user)` en los 4 endpoints existentes.
`/webhooks/*` (spec 006/007) se queda público — Telegram no tiene ni puede tener un JWT nuestro; ya
tiene su propio control de acceso (`verify_telegram_secret`). División explícita:

| Prefijo | Protección |
|---|---|
| `/webhooks/*` | `verify_telegram_secret` (secreto compartido, no JWT) |
| `/auth/google/*` | Pública (es el propio mecanismo de login) |
| `/auth/me`, `/organizations/*` | `get_current_user()` (JWT obligatorio) |
| `/health*` | Pública (liveness/readiness, sin datos sensibles) |

---

## 9. Google OpenID Connect — alcance exacto

El MVP acepta **cualquier cuenta de Google**, no solo cuentas corporativas de un dominio
específico — no hay Google Workspace gestionado en Amza Empaques hoy. Esto es deliberado, no una
limitación temporal a corregir: el protocolo (Google OpenID Connect) no cambia el día que exista
un Workspace — solo cambiaría la *política* (por ejemplo, restringir por el claim `hd` si algún
día aplica). No se documenta como "cuentas personales de Google" porque eso describe el estado
actual de una decisión de negocio, no el diseño del sistema.

**El frontend nunca habla con Google directamente.** Todo el intercambio OAuth vive en el backend:

```
Next.js → Backend (/auth/google/login) → Google → Backend (/auth/google/callback) → JWT → Frontend
```

Nunca `Next.js → Google → Backend`. Razón: el `client_secret` nunca debe existir en código que
corre en el navegador, y centralizar la integración OAuth en el backend significa que agregar
Microsoft (o cualquier otro proveedor) el día de mañana no le cambia nada al frontend — solo un
nuevo `AuthProvider` y una nueva ruta `/auth/microsoft/*` en el backend.

---

## 10. Identificador de autenticación: email, no `sub`

El email es la clave de dominio — es lo único que un administrador puede conocer *antes* de que la
persona inicie sesión por primera vez (el `sub` de Google no existe todavía en ese momento, y
tampoco sirve como clave universal: el `sub` de Microsoft para la misma persona sería un valor
completamente distinto). Consecuencia explícita, aceptada: **si el email de Google de alguien
cambia, un administrador debe actualizar `InternalUser.email` a mano** — no hay sincronización
automática ni se guarda el `sub` para resolverlo solo. A esta escala (pocos usuarios internos), es
la opción más simple y suficientemente robusta.

`InternalUser.email` must be unique (case-insensitive) — ver regla de normalización y el índice
único en la sección 1.

---

## Future Evolution (Not part of this specification)

| Item | Alcance | Se aborda cuando... |
|---|---|---|
| `MicrosoftOAuthProvider` | Segunda implementación de `AuthProvider`, misma interfaz | Amza Empaques (u otra organización futura) lo pida explícitamente |
| Revocación de JWT | Lista de revocación o tokens de corta vida + refresh | El límite de 24h de exposición tras desactivar un usuario deje de ser aceptable |
| Restricción de dominio (`hd` claim) | Limitar login a un Workspace específico | Amza Empaques adopte Google Workspace gestionado |
| `CustomerMemory`, Knowledge Base, etc. | Ya registrado en spec 006 | Sin cambios — no relacionado con este spec |

---

## Próximo paso

Con 008, la plataforma deja de estar abierta al público. El siguiente paso natural es spec 009 —
el frontend de asesor (login vía `/auth/google/login`, dashboard de oportunidades, historial de
conversación) — ahora sí tiene con qué autenticarse.

Política de ingeniería a partir de este spec (acuerdo, no un spec propio): toda especificación
nueva debe incluir pruebas automatizadas del comportamiento que introduce; si una especificación
modifica comportamiento existente, también debe actualizar las pruebas afectadas. La deuda de
tests de specs 002-007 queda registrada como deuda conocida, no resuelta retroactivamente de golpe.
