# MVP Specification – 003 Persistence Model

## Objetivo

Este documento define cómo el modelo de dominio será persistido.

No representa todavía una implementación específica mediante SQLAlchemy o SQLite.

Su propósito consiste en traducir el dominio del negocio a un modelo de persistencia consistente, mantenible y preparado para evolucionar.

---

# Principios

La persistencia deberá cumplir los siguientes principios.

* Respetar completamente el modelo del dominio.
* Evitar duplicación innecesaria.
* Mantener la integridad de los datos.
* Facilitar futuras migraciones.
* Mantener independencia respecto al motor de base de datos.

---

# Entidades persistentes

Durante el MVP deberán persistirse las siguientes entidades.

## Organization

Información de la empresa propietaria del sistema.

Aunque inicialmente existirá una única Organization, deberá mantenerse como entidad persistente para facilitar la evolución a múltiples organizaciones.

---

## Internal User

Usuarios que acceden al Dashboard.

Información mínima:

* identidad;
* rol;
* credenciales;
* estado.

---

## AI Assistant

Configuración del asistente.

Ejemplos.

* nombre;
* modelo utilizado;
* parámetros;
* estado.

No almacenará conversaciones.

---

## Contact

Información básica del contacto.

Ejemplos.

* nombre;
* teléfono;
* canal principal;
* empresa;
* información adicional.

---

## Customer

Extensión comercial de un Contact.

Inicialmente podrá representarse mediante un atributo del Contact.

No requiere una entidad independiente durante el MVP.

---

## Opportunity

Entidad principal del sistema.

Toda Opportunity deberá persistir como mínimo.

* estado;
* fecha de creación;
* fecha de actualización;
* responsable actual;
* prioridad;
* origen;
* información comercial relevante.

---

## Conversation

Cada Opportunity tendrá una Conversation persistente.

La Conversation conservará el historial completo.

---

## Message

Todos los mensajes deberán persistirse.

Cada Message almacenará.

* contenido;
* tipo;
* remitente;
* fecha;
* metadatos relevantes.

---

## Assignment

Historial de asignaciones entre AI Assistant y Advisors.

Permitirá reconstruir quién atendió una Opportunity en cualquier momento.

---

## Quotation

Cada cotización deberá conservarse.

Información mínima.

* fecha;
* versión;
* estado;
* monto;
* observaciones.

---

## Follow-up

Toda actividad de seguimiento deberá persistirse.

Ejemplos.

* fecha programada;
* responsable;
* estado;
* notas.

---

## Product

Catálogo comercial.

---

## Product Variant

Variantes comerciales de un Product.

---

## Asset

Recursos digitales utilizados por el negocio.

El sistema almacenará únicamente su información y ubicación.

Los archivos físicos podrán residir en almacenamiento externo.

---

## Business Rule

Representación persistente de reglas comerciales configurables.

Inicialmente podrá mantenerse sencilla.

---

# Relaciones principales

Organization

↓

Internal Users

Organization

↓

AI Assistants

Organization

↓

Products

↓

Variants

Organization

↓

Assets

Organization

↓

Business Rules

Organization

↓

Opportunities

↓

Conversation

↓

Messages

↓

Quotations

↓

Follow-ups

↓

Assignments

Opportunity

↓

Contact

---

# Integridad

Toda entidad deberá poseer un identificador único.

Las relaciones obligatorias deberán garantizarse mediante restricciones de integridad.

No deberán existir registros huérfanos.

---

# Historial

El sistema privilegiará conservar información antes que eliminarla.

Siempre que sea posible.

* registrar cambios;
* mantener historial;
* evitar pérdidas de información comercial.

---

# Eliminación

Durante el MVP se utilizará Soft Delete únicamente cuando aporte valor real.

La eliminación física deberá evitarse para información comercial relevante.

---

# Auditoría

Las entidades principales deberán almacenar.

* fecha de creación;
* fecha de modificación.

En futuras versiones podrán incorporarse auditorías completas.

---

# Persistencia de archivos

Los Assets no deberán almacenarse directamente en la base de datos.

La base de datos únicamente conservará.

* nombre;
* tipo;
* ubicación;
* metadatos.

---

# Persistencia del conocimiento

El Business Knowledge podrá provenir de múltiples fuentes.

La base de datos representa únicamente una de ellas.

La arquitectura nunca deberá asumir que todo el conocimiento reside en SQLite.

---

# Transacciones

Las operaciones que modifiquen una Opportunity y sus elementos relacionados deberán ejecutarse dentro de una única transacción lógica mediante Unit of Work.

---

# Escalabilidad

Aunque el MVP utilizará SQLite, el modelo deberá migrar a PostgreSQL sin modificaciones significativas del dominio.

La persistencia nunca deberá incorporar características exclusivas de un motor específico.

---

# Principio final

El modelo de persistencia existe para servir al dominio.

Nunca al contrario.

---

# Implementación técnica

## Objetivo

Crear la capa de persistencia utilizando SQLAlchemy 2.x con soporte asíncrono.

Los modelos ORM son clases completamente independientes de las entidades del dominio definidas en `core/`.

Los modelos ORM únicamente representan cómo se almacenan los datos.

Las reglas del negocio nunca viven aquí.

---

## Nueva dependencia

Agregar al bloque `dependencies` de `backend/pyproject.toml`:

```
aiosqlite>=0.20.0
```

Esta librería es el driver async de SQLite requerido por SQLAlchemy para operar en modo asíncrono.

Para PostgreSQL en producción se usará `asyncpg` — sin modificar nada más del código.

Reinstalar después de agregar:

```bash
pip install -e ".[dev]"
```

---

## Regla fundamental

Los modelos ORM pueden importar desde `core/`.

`core/` nunca deberá importar desde `infrastructure/` ni desde `modules/`.

La dependencia siempre apunta hacia el dominio, nunca en sentido contrario.

---

## Estructura de archivos

Los archivos nuevos o modificados en esta especificación son los siguientes.

```
backend/
├── pyproject.toml                              (agregar aiosqlite)
│
├── infrastructure/
│   └── database/
│       ├── base.py                             (DeclarativeBase compartida)
│       ├── engine.py                           (AsyncEngine desde config)
│       └── session.py                          (AsyncSession factory)
│
├── modules/
│   ├── configuration/
│   │   └── models/
│   │       └── organization.py                 (OrganizationModel)
│   ├── opportunities/
│   │   └── models/
│   │       ├── contact.py                      (ContactModel)
│   │       ├── opportunity.py                  (OpportunityModel)
│   │       ├── conversation.py                 (ConversationModel)
│   │       └── message.py                      (MessageModel)
│   ├── users/
│   │   └── models/
│   │       └── internal_user.py                (InternalUserModel)
│   └── agents/
│       └── models/
│           └── agent.py                        (AgentModel)
│
└── migrations/
    ├── env.py                                  (actualizar target_metadata)
    └── versions/
        └── 0001_initial_schema.py              (migración autogenerada)
```

Los `__init__.py` de todos estos directorios ya existen desde la especificación 001.

Solo se requiere agregar contenido a los archivos listados.

---

## infrastructure/database/base.py

Define la clase base de la que heredarán todos los modelos ORM.

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Ningún modelo deberá importar `DeclarativeBase` directamente desde SQLAlchemy.

Todos los modelos deberán heredar de esta `Base`.

---

## infrastructure/database/engine.py

Crea el `AsyncEngine` leyendo la URL desde la configuración de la aplicación.

La URL en `.env` usa el prefijo `sqlite:///`. Para el driver async, este módulo transforma la URL a `sqlite+aiosqlite:///` antes de crear el engine.

Este módulo es el único lugar del proyecto donde ocurre esa transformación.

El engine se crea con `echo=settings.debug` para que las queries SQL aparezcan en el log cuando `DEBUG=true`.

---

## infrastructure/database/session.py

Expone dos cosas:

**`AsyncSessionFactory`** — un `async_sessionmaker` configurado con `expire_on_commit=False`.

`expire_on_commit=False` evita que SQLAlchemy invalide los objetos al confirmar una transacción. Sin esta configuración, acceder a atributos de un objeto después del commit lanzaría un error de lazy-load.

**`get_session`** — generador asíncrono para usar como dependencia en FastAPI.

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
```

---

## Convenciones de todos los modelos ORM

**Tipos de columna:**

| Concepto | Tipo SQLAlchemy |
|---|---|
| UUID (primary key y foreign keys) | `sa.Uuid(native_uuid=False)` |
| Texto corto (nombres, slugs, roles, enums) | `sa.String(N)` con longitud apropiada |
| Texto largo (contenido de mensajes, descripciones) | `sa.Text` |
| Fechas con timezone | `sa.DateTime(timezone=True)` |
| JSON (metadata) | `sa.JSON` |

**Regla de enums:** los modelos ORM almacenan el `.value` del enum como `String(50)`.

No utilizar `sa.Enum(PythonEnum)`.

Por qué: `sa.Enum` genera columnas `ENUM` en PostgreSQL que requieren `ALTER TYPE` para agregar valores — un problema en producción. Con `String` cualquier nuevo valor del enum se agrega sin migración de columna.

**Regla de nullable:** todas las columnas son `NOT NULL` por defecto. Solo se marca `nullable=True` cuando el campo del dominio admite `None`.

**Regla de UUIDs:** usar `sa.Uuid(native_uuid=False)` en todos los IDs.

Con `native_uuid=False`, SQLAlchemy almacena el UUID como string de 36 caracteres en SQLite y como UUID nativo en PostgreSQL — sin cambios en el código de la aplicación.

---

## Modelos ORM

### modules/configuration/models/organization.py

Clase: `OrganizationModel`

Tabla: `organizations`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `name` | `String(255)` | not null |
| `slug` | `String(100)` | not null, unique |
| `timezone` | `String(50)` | not null |
| `language` | `String(10)` | not null |
| `status` | `String(50)` | not null |
| `created_at` | `DateTime(timezone=True)` | not null |
| `updated_at` | `DateTime(timezone=True)` | not null |

Índice sobre `slug`.

---

### modules/opportunities/models/contact.py

Clase: `ContactModel`

Tabla: `contacts`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `organization_id` | `Uuid` | not null, FK → organizations.id |
| `channel_type` | `String(50)` | not null |
| `external_id` | `String(255)` | not null |
| `display_name` | `String(255)` | not null |
| `status` | `String(50)` | not null |
| `created_at` | `DateTime(timezone=True)` | not null |
| `updated_at` | `DateTime(timezone=True)` | not null |

Restricción única compuesta: `(external_id, channel_type, organization_id)`.

Índices: `organization_id`, `external_id`.

La restricción única garantiza que el mismo contacto externo (por ejemplo, el mismo `chat_id` de Telegram) no se registre dos veces en la misma organización y canal.

---

### modules/users/models/internal_user.py

Clase: `InternalUserModel`

Tabla: `internal_users`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `organization_id` | `Uuid` | not null, FK → organizations.id |
| `name` | `String(255)` | not null |
| `email` | `String(255)` | not null, unique |
| `role` | `String(50)` | not null |
| `status` | `String(50)` | not null |
| `created_at` | `DateTime(timezone=True)` | not null |
| `updated_at` | `DateTime(timezone=True)` | not null |

Índice sobre `organization_id`.

---

### modules/agents/models/agent.py

Clase: `AgentModel`

Tabla: `agents`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `organization_id` | `Uuid` | not null, FK → organizations.id |
| `name` | `String(255)` | not null |
| `description` | `Text` | not null |
| `status` | `String(50)` | not null |
| `created_at` | `DateTime(timezone=True)` | not null |
| `updated_at` | `DateTime(timezone=True)` | not null |

Índices: `organization_id`, `status`.

---

### modules/opportunities/models/opportunity.py

Clase: `OpportunityModel`

Tabla: `opportunities`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `organization_id` | `Uuid` | not null, FK → organizations.id |
| `contact_id` | `Uuid` | not null, FK → contacts.id |
| `agent_id` | `Uuid` | not null, FK → agents.id |
| `attention_mode` | `String(50)` | not null |
| `assigned_advisor_id` | `Uuid` | nullable, FK → internal_users.id |
| `status` | `String(50)` | not null |
| `channel_type` | `String(50)` | not null |
| `started_at` | `DateTime(timezone=True)` | not null |
| `last_activity_at` | `DateTime(timezone=True)` | not null |
| `closed_at` | `DateTime(timezone=True)` | nullable |

Índices: `organization_id`, `contact_id`, `agent_id`, `status`, `last_activity_at`.

---

### modules/opportunities/models/conversation.py

Clase: `ConversationModel`

Tabla: `conversations`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `opportunity_id` | `Uuid` | not null, FK → opportunities.id, unique |
| `created_at` | `DateTime(timezone=True)` | not null |
| `updated_at` | `DateTime(timezone=True)` | not null |

`opportunity_id` es `unique` porque una Opportunity tiene exactamente una Conversation activa.

Índice sobre `opportunity_id`.

---

### modules/opportunities/models/message.py

Clase: `MessageModel`

Tabla: `messages`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `Uuid` | primary key |
| `conversation_id` | `Uuid` | not null, FK → conversations.id |
| `role` | `String(50)` | not null |
| `content_type` | `String(50)` | not null |
| `content` | `Text` | not null |
| `created_at` | `DateTime(timezone=True)` | not null |
| `provider_message_id` | `String(255)` | nullable |
| `metadata` | `JSON` | not null, server_default `'{}'` |

Índices: `conversation_id`, `created_at`, `provider_message_id`.

`metadata` almacena datos específicos del canal (Telegram `update_id`, WhatsApp `webhook_id`, etc.) que nunca se consultan con lógica de negocio.

---

## Actualización de migrations/env.py

El archivo `migrations/env.py` actualmente tiene `target_metadata = None`.

Deberá actualizarse para:

1. Importar `Base` desde `infrastructure.database.base`.
2. Importar todos los modelos ORM — aunque no se usen directamente en `env.py`, este import los registra en `Base.metadata`.
3. Asignar `target_metadata = Base.metadata`.

Sin estos imports, Alembic no detectará las tablas al autogenerar migraciones.

El orden de imports en `env.py` deberá ser:

```python
from infrastructure.database.base import Base
from modules.configuration.models.organization import OrganizationModel  # noqa: F401
from modules.opportunities.models.contact import ContactModel  # noqa: F401
from modules.opportunities.models.opportunity import OpportunityModel  # noqa: F401
from modules.opportunities.models.conversation import ConversationModel  # noqa: F401
from modules.opportunities.models.message import MessageModel  # noqa: F401
from modules.users.models.internal_user import InternalUserModel  # noqa: F401
from modules.agents.models.agent import AgentModel  # noqa: F401
```

El comentario `# noqa: F401` suprime la advertencia de "import no utilizado" de ruff, que de otro modo marcaría estos imports como error.

---

## Primera migración

Después de implementar los modelos y actualizar `env.py`, generar la migración:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
```

El archivo se genera automáticamente en `migrations/versions/`.

Renombrarlo a `0001_initial_schema.py` por convención de nomenclatura del proyecto.

Verificar que el archivo generado contenga las siguientes tablas en `upgrade()` en este orden (respetando las foreign keys):

1. `organizations`
2. `contacts`
3. `internal_users`
4. `agents`
5. `opportunities`
6. `conversations`
7. `messages`

Y que `downgrade()` las elimine en orden inverso.

Aplicar la migración:

```bash
alembic upgrade head
```

Esto crea el archivo `data/amza.db` con el schema completo.

---

## Lo que NO debe hacerse

* No agregar lógica de negocio a los modelos ORM.
* No definir `relationship()` en esta especificación — las relaciones SQLAlchemy se agregarán cuando los repositories las necesiten.
* No modificar archivos dentro de `core/`.
* No crear endpoints ni servicios — solo la capa de persistencia.
* No usar `sa.Enum(PythonEnum)` para columnas de enum.

---

## Definición de terminado

La tarea se considerará terminada cuando:

* `aiosqlite` esté en `pyproject.toml` e instalado.
* Los 3 archivos de `infrastructure/database/` existan.
* Los 7 modelos ORM existan con los campos y restricciones definidos en este documento.
* `migrations/env.py` apunte a `Base.metadata` con todos los modelos importados.
* El archivo `0001_initial_schema.py` exista en `migrations/versions/` con las 7 tablas.
* `alembic upgrade head` ejecute sin errores y cree `data/amza.db`.
* `ruff check .` pase sin errores desde `backend/`.
* `mypy app core infrastructure` pase sin errores desde `backend/`.

---

## Principio fundamental

Los modelos ORM son detalles de implementación.

Representan cómo se almacena la información, no qué significa esa información.

El significado vive en `core/`.

El almacenamiento vive aquí.

Mantenerlos separados garantiza que cambiar de SQLite a PostgreSQL nunca requiera tocar las reglas del negocio.

