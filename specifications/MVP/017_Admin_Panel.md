# 017 Admin Panel

## Propósito

Cierra la pantalla `/admin` (spec 011 la dejó como placeholder, spec 014 ya le agregó la sección
de Usuarios) con las dos piezas que faltaban del pedido original: editar el prompt del agente
(principal + reglas de escalamiento) y conectar/desconectar WhatsApp — lo que spec 016
deliberadamente dejó fuera, usando `WhatsAppChannelProvider.health()` para saber cuándo
mostrarlo.

**Explícitamente fuera de alcance:**

- Cambiar el bot token de Telegram desde la UI — sigue siendo `.env` +
  `scripts/register_telegram_webhook.py` (spec 007). Editar un token en vivo implicaría
  reconstruir `TelegramChannelProvider` en caliente (hoy singleton vía `@lru_cache`, spec 006) sin
  ningún beneficio real: el token casi nunca cambia, y el flujo por script ya funciona. Distinto
  del caso de WhatsApp (sección 3): ahí "cambiar el número" *es* desconectar y volver a vincular
  por QR — una operación de Evolution API, no de nuestra configuración.
- Base de conocimiento y multimedia — specs 018/019.
- Cualquier regla de escalamiento *estructurada* (que la IA misma decida ceder el control por una
  señal explícita, no solo texto) — hoy no existe ningún mecanismo así (`OpenRouterAIProvider`
  nunca cambia `attention_mode`, solo un humano lo hace al "Tomar conversación"). Este spec edita
  **texto** que ya viaja al modelo como instrucciones, no construye ese mecanismo.

---

## 1. `Agent.escalation_rules` — separar el prompt en dos campos

Hoy "reglas de escalamiento" no existe como concepto propio — es lo que sea que alguien haya
escrito dentro de `Agent.system_prompt`. Se separa en un segundo campo de texto, no porque cambie
cómo el modelo las recibe (las dos partes se concatenan igual al armar el mensaje de sistema),
sino porque un administrador editando el prompt necesita distinguir "cómo debe hablar el agente"
de "cuándo debe ceder a un humano" sin desenredar un solo bloque de texto cada vez.

`core/entities/agent.py`:

```python
escalation_rules: str = ""
```

Migración `0006_add_agent_escalation_rules`:

```python
def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("escalation_rules", sa.Text(), nullable=False, server_default=""),
    )
```

`infrastructure/ai/openrouter.py::generate()` — el mensaje de sistema concatena ambos campos, en
vez de solo `agent.system_prompt`:

```python
system_content = agent.system_prompt
if agent.escalation_rules:
    system_content += f"\n\n---\nCuándo derivar a un humano:\n{agent.escalation_rules}"
if context.summary:
    system_content += f"\n\n---\nResumen de la conversación:\n{context.summary}"
```

(Orden: prompt principal, luego reglas de escalamiento, luego resumen — el resumen va al final
porque es lo más específico de la conversación actual, mismo criterio que ya tenía el código.)

---

## 2. Editar el agente — `GET`/`PUT /organizations/{slug}/agent`

Un único agente por organización ya existe como concepto (`AgentRepository.get_default_by_organization`,
spec 004) — no hace falta gestionar varios, ninguna parte del producto lo pidió.

`app/use_cases/get_agent.py` / `update_agent.py`:

```python
class UpdateAgentUseCase:
    async def execute(
        self,
        organization_slug: str,
        system_prompt: str,
        escalation_rules: str,
        model: str,
    ) -> Agent:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            agent = await uow.agents.get_default_by_organization(organization.id)
            if agent is None:
                raise NoActiveAgentError(organization.id)

            agent.system_prompt = system_prompt
            agent.escalation_rules = escalation_rules
            agent.model = model
            agent.updated_at = datetime.now(tz=UTC)
            await uow.agents.save(agent)
            await uow.commit()
        return agent
```

`app/api/dto/agent.py` (nuevo): `AgentResponse{id, name, system_prompt, escalation_rules, model}`,
`UpdateAgentRequest{system_prompt, escalation_rules, model}`.

`app/api/routers/agent.py` (nuevo), protegido con `require_role(InternalUserRole.ADMINISTRATOR)`
(mismo criterio que `/users` en spec 014 — cambiar cómo responde la IA no es una acción de
asesor):

```python
router = APIRouter(
    prefix="/organizations/{organization_slug}/agent",
    tags=["agent"],
    dependencies=[Depends(require_role(InternalUserRole.ADMINISTRATOR))],
)


@router.get("")
async def get_agent(...) -> AgentResponse: ...


@router.put("")
async def update_agent(...) -> AgentResponse: ...
```

Sin versionado ni historial de cambios del prompt — no se pidió, y sería la primera entidad del
proyecto en necesitarlo; se revisita si en la práctica hace falta poder revertir un cambio.

---

## 3. WhatsApp — conectar/desconectar desde `/admin`

Evolution API expone lo necesario (confirmado contra su documentación real, igual que en spec
016): `GET /instance/connect/{instance}` devuelve un QR nuevo para (re)vincular, `DELETE
/instance/logout/{instance}` desvincula sin borrar la instancia. `WhatsAppChannelProvider`
(spec 016) gana dos métodos — **no** parte del `ChannelProvider` Protocol (son operaciones de
administración de la instancia, no de mensajería; `TelegramChannelProvider` no las necesita, igual
que no necesita `start()`/`stop()`):

```python
class WhatsAppChannelProvider:
    ...
    async def get_qr_code(self) -> str:
        response = await self._client.get(f"/instance/connect/{self._instance_name}")
        response.raise_for_status()
        return str(response.json()["base64"])

    async def disconnect(self) -> None:
        response = await self._client.delete(f"/instance/logout/{self._instance_name}")
        response.raise_for_status()
```

`app/api/routers/whatsapp_admin.py` (nuevo), también protegido con
`require_role(InternalUserRole.ADMINISTRATOR)`:

| Método y ruta | Acción |
|---|---|
| `GET /organizations/{slug}/whatsapp/status` | `{"connected": bool}` — delega en `WhatsAppChannelProvider.health()` (spec 016), sin duplicar esa lógica |
| `POST /organizations/{slug}/whatsapp/connect` | `{"qrcode_base64": str}` — llama a `get_qr_code()` |
| `POST /organizations/{slug}/whatsapp/disconnect` | `204` — llama a `disconnect()` |

El provider se obtiene del mismo `ChannelProviderRegistry` (spec 015) que ya usan los casos de
uso de mensajería —`registry.get(ChannelType.WHATSAPP)`, con el mismo `isinstance` que ya usa
`app/lifecycle.py` para distinguirlo de otros providers antes de llamar métodos que no son parte
del Protocol genérico.

**Mantener la sesión activa** (pedido explícito desde el principio de esta tanda: "evitar
escanear o reconectar el código QR constantemente") — esta pantalla nunca reconecta sola. El botón
"Conectar" solo se habilita cuando `GET .../status` devuelve `connected: false` — no hay
temporizador que lo intente de nuevo automáticamente, mostrarlo es una acción deliberada del
administrador, no un proceso en segundo plano.

---

## 4. Frontend — `/admin` gana dos secciones

`frontend/app/(workspace)/admin/page.tsx` (spec 014 ya reemplazó el placeholder con la tabla de
usuarios) — se reorganiza en pestañas: **Usuarios** (spec 014, sin cambios), **Agente** (nueva),
**Canales** (nueva).

**Agente**: dos `<textarea>` (prompt principal, reglas de escalamiento) + selector de modelo +
botón "Guardar" (`useAgent()`/`useUpdateAgent()`, nuevos hooks). Sin autoguardado — un prompt mal
guardado a mitad de escritura afecta a la IA respondiéndole a clientes reales de inmediato, el
guardado debe ser una acción explícita.

**Canales**: por cada canal (`ChannelType.TELEGRAM`, `ChannelType.WHATSAPP`):
- Telegram: solo lectura — "Configurado" (no hay nada que esta pantalla pueda cambiar, ver
  "Fuera de alcance").
- WhatsApp: insignia Conectado/Desconectado (`useWhatsAppStatus()`, refresco manual con un botón,
  no polling automático — coherente con "nunca reconectar sola" de la sección 3); si desconectado,
  botón "Conectar" que llama `useConnectWhatsApp()` y muestra el QR devuelto (una imagen
  `data:image/png;base64,...`, se cierra el diálogo solo cuando el administrador lo cierra —
  ninguna detección automática de "ya se escaneó", coherente con no meter polling); si conectado,
  botón "Desconectar" con una confirmación (es destructivo — corta el servicio a clientes reales
  de WhatsApp hasta que alguien vuelva a escanear).

---

## 5. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- Backend (`tests/test_admin_panel.py`, nuevo):
  1. `PUT .../agent` actualiza `system_prompt`/`escalation_rules`/`model`; `GET .../agent`
     devuelve los valores guardados.
  2. Un Advisor autenticado llama cualquier endpoint de `/agent` o `/whatsapp/*` → 403
     (`require_role`, mismo patrón que spec 014).
  3. Regresión sobre `OpenRouterAIProvider.generate()`: con `escalation_rules` no vacío, el
     mensaje de sistema enviado a OpenRouter incluye ambos bloques, en el orden documentado en la
     sección 1 (capturar el payload real vía fake `httpx` transport, mismo patrón que el test de
     regresión de spec 010).
  4. `GET .../whatsapp/status` refleja `WhatsAppChannelProvider.health()` (fake provider,
     `connected: true`/`false` según el estado simulado).
  5. `POST .../whatsapp/connect` devuelve el `base64` que responde el fake de Evolution API;
     `POST .../whatsapp/disconnect` → 204 y llama `DELETE /instance/logout/...` exactamente una
     vez.
- Frontend (extender `frontend/tests/e2e/`): un administrador edita el prompt y lo guarda, ve
  reflejado el valor tras recargar; ve el estado de WhatsApp y, si está desconectado, ve aparecer
  el QR al pulsar "Conectar" (mockeado, sin Evolution API real).

---

## Próximo paso

Spec 018 — **Knowledge Base**: subida de archivos (listas de precios, fichas técnicas) que la IA
usa como insumo de contexto al responder — el primer spec de esta tanda que le da a la IA acceso a
datos que hoy no tiene, en vez de solo rediseñar cómo se muestra lo que ya existe.
