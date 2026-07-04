# MVP Specification – 002 Business Domain Model

## Objetivo

Este documento define el modelo de dominio del negocio.

No describe tablas de base de datos.

No describe clases.

No describe APIs.

Su propósito consiste en representar correctamente el funcionamiento del negocio para que la implementación técnica sea una consecuencia natural del dominio.

Todas las decisiones de implementación deberán respetar este modelo.

---

# Filosofía

La plataforma no administra chats.

La plataforma administra oportunidades comerciales.

Las conversaciones representan únicamente el medio mediante el cual una oportunidad evoluciona.

El dominio completo gira alrededor de una Opportunity.

---

# Aggregate Root Principal

## Opportunity

La Opportunity representa una posible venta.

Es el elemento central del dominio.

Toda la información relevante del proceso comercial se relaciona directa o indirectamente con una Opportunity.

Una Opportunity puede contener:

* un Contact;
* una Conversation;
* múltiples Messages;
* cero o más Quotations;
* cero o más Follow-ups;
* un estado comercial;
* un responsable actual.

Toda operación importante del negocio deberá iniciar desde una Opportunity.

---

# Organization

Representa una empresa que utiliza la plataforma.

Una Organization contiene:

* Internal Users;
* AI Assistants;
* Products;
* Assets;
* Business Knowledge;
* Opportunities;
* Channels.

En el MVP existirá una única Organization.

La arquitectura deberá soportar múltiples organizaciones en el futuro.

---

# Internal User

Persona perteneciente a la Organization.

Utiliza el Dashboard.

Puede asumir distintos roles.

Inicialmente:

* Advisor
* Administrator

---

# Advisor

Empleado encargado de atender oportunidades que requieren criterio humano, también llamado Human.

El Advisor puede asumir el control de cualquier Opportunity.

---

# AI Assistant

Asistente responsable de atender automáticamente consultas repetitivas.

El AI Assistant pertenece a una Organization.

Nunca pertenece a una Opportunity específica.

Una Opportunity podrá ser atendida temporalmente por un AI Assistant.

---

# Contact

Persona que inicia una conversación con la empresa.

Todo Contact podrá convertirse posteriormente en Customer.

---

# Customer

Contact que ya realizó al menos una compra.

Todos los Customers son Contacts.

No todos los Contacts son Customers.

---

# Conversation

Representa el historial completo de comunicación asociado a una Opportunity.

Una Opportunity tendrá una única Conversation activa.

Toda la comunicación deberá conservarse.

---

# Message

Unidad mínima de comunicación.

Un Message pertenece siempre a una Conversation.

Puede ser:

* texto;
* imagen;
* video;
* documento;
* audio;
* ubicación;
* otros formatos soportados por el Channel.

---

# Opportunity Status

Toda Opportunity deberá encontrarse exactamente en uno de los siguientes estados.

* New
* Qualified
* Waiting for Advisor
* Quotation Pending
* Quotation Sent
* Follow-up Pending
* Won
* Lost
* Closed

Los estados representan la evolución comercial de la oportunidad.

No representan el estado de la conversación.

---

# Assignment

Representa quién posee actualmente la responsabilidad de atender una Opportunity.

El Assignment podrá corresponder a:

* AI Assistant
* Advisor

El propietario podrá cambiar múltiples veces durante el ciclo de vida de la Opportunity.

El cliente nunca deberá percibir este cambio.

---

# Quotation

Representa una propuesta comercial enviada al Contact.

Una Opportunity podrá contener múltiples Quotations.

Cada Quotation deberá conservar su historial.

---

# Follow-up

Representa una actividad posterior realizada con el objetivo de aumentar la probabilidad de cerrar una venta.

Una Opportunity podrá contener múltiples Follow-ups.

El sistema deberá ayudar a identificar cuáles requieren atención.

---

# Product

Artículo comercializado por la Organization.

Un Product podrá contener múltiples Product Variants.

---

# Product Variant

Versión específica de un Product.

Podrá variar por:

* tamaño;
* material;
* capacidad;
* acabado;
* otras características comerciales.

---

# Product Customization

Representa una modificación solicitada por el cliente.

Existen dos categorías.

## Standard Customization

Personalización de un Product existente sin modificar su estructura.

Podrá ser atendida automáticamente cuando existan reglas definidas.

---

## Custom Development

Creación de un nuevo producto o modificación estructural.

Requerirá inicialmente intervención humana.

---

# Asset

Recurso digital utilizado durante la atención comercial.

Ejemplos.

* imágenes;
* videos;
* catálogos;
* fichas técnicas;
* documentos PDF.

Los Assets forman parte del Business Knowledge.

---

# Business Knowledge

Conjunto de información utilizada para responder correctamente las consultas.

Puede provenir de:

* catálogo;
* archivos Excel;
* reglas comerciales;
* documentos;
* SIIGO;
* futuras integraciones.

El AI Assistant nunca deberá asumir el origen del conocimiento.

---

# Channel

Representa el origen de una Conversation.

Ejemplos.

* Telegram
* WhatsApp
* Instagram
* Facebook Messenger

La Opportunity nunca dependerá de un Channel específico.

---

# Relaciones del dominio

Organization

↓

Opportunities

↓

Conversation

↓

Messages

Organization

↓

Business Knowledge

↓

Products

↓

Variants

↓

Assets

Organization

↓

Internal Users

↓

Advisor

Organization

↓

AI Assistants

---

# Principios del dominio

El dominio representa el negocio.

Nunca deberá modificarse para facilitar una implementación técnica.

Si existe un conflicto entre el dominio y la tecnología, deberá adaptarse la tecnología.

Nunca el negocio.

Todo cambio del modelo de dominio deberá reflejar una evolución real del negocio y no una necesidad accidental de implementación.

---

# Implementación técnica

## Objetivo

Traducir el modelo de dominio a código Python puro ubicado exclusivamente en `core/`.

Ninguna entidad del dominio deberá depender de SQLAlchemy, Pydantic, FastAPI ni de ningún framework externo.

---

## Regla fundamental

Los únicos módulos permitidos dentro de `core/` son los de la biblioteca estándar de Python.

`core/` nunca deberá importar:

* SQLAlchemy
* Pydantic
* FastAPI
* httpx
* structlog
* ningún módulo de `infrastructure/`, `modules/` ni `app/`

Las dependencias permitidas son exclusivamente:

* `uuid`
* `datetime`
* `enum`
* `dataclasses`
* `typing`

Si en algún momento se requiere importar algo externo dentro de `core/`, es señal de que algo está mal en el diseño.

---

## Estructura de archivos

```
core/
├── enums/
│   ├── __init__.py
│   ├── opportunity.py
│   ├── message.py
│   ├── channel.py
│   ├── agent.py
│   └── user.py
├── value_objects/
│   ├── __init__.py
│   └── identifiers.py
├── entities/
│   ├── __init__.py
│   ├── organization.py
│   ├── contact.py
│   ├── internal_user.py
│   ├── agent.py
│   ├── opportunity.py
│   ├── conversation.py
│   └── message.py
├── events/
│   ├── __init__.py
│   └── opportunity.py
├── interfaces/
│   ├── __init__.py
│   ├── repositories.py
│   └── providers.py
└── exceptions/
    ├── __init__.py
    └── domain.py
```

Todos los archivos `__init__.py` ya existen desde la especificación 001.

Solo se requiere agregar contenido a los archivos correspondientes.

---

## Enums

Los enums representan los estados y categorías fijos del dominio.

Todos utilizan `enum.Enum` o `enum.StrEnum` según corresponda.

### core/enums/opportunity.py

**OpportunityStatus** — estado comercial de la oportunidad:

* `NEW` — recién creada, sin calificar
* `QUALIFIED` — confirmada como oportunidad real
* `WAITING_FOR_ADVISOR` — escalada, esperando atención humana
* `QUOTATION_PENDING` — requiere cotización
* `QUOTATION_SENT` — cotización enviada al contacto
* `FOLLOW_UP_PENDING` — requiere seguimiento
* `WON` — venta cerrada exitosamente
* `LOST` — oportunidad perdida
* `CLOSED` — cerrada sin resultado comercial definitivo

**AttentionMode** — quién controla actualmente la conversación:

* `AI` — el AI Assistant responde automáticamente
* `HUMAN` — un Advisor tiene el control

### core/enums/message.py

**MessageRole** — quién envió el mensaje:

* `USER` — el contacto externo
* `ASSISTANT` — el AI Assistant o el Advisor
* `SYSTEM` — mensaje interno del sistema, nunca visible al contacto

**MessageContentType** — tipo de contenido del mensaje:

* `TEXT`
* `IMAGE`
* `VIDEO`
* `DOCUMENT`
* `AUDIO`
* `LOCATION`

### core/enums/channel.py

**ChannelType** — canal de mensajería de origen:

* `TELEGRAM`
* `WHATSAPP`
* `INSTAGRAM`
* `FACEBOOK_MESSENGER`

### core/enums/agent.py

**AgentStatus** — estado operativo del AI Assistant:

* `ACTIVE` — responde normalmente
* `PAUSED` — no responde automáticamente
* `DISABLED` — no acepta nuevas conversaciones
* `MAINTENANCE` — responde indicando que está temporalmente fuera de servicio

### core/enums/user.py

**InternalUserRole** — rol del usuario interno:

* `ADVISOR` — atiende conversaciones
* `ADMINISTRATOR` — administra la plataforma

**InternalUserStatus** — estado del usuario interno:

* `ACTIVE`
* `INACTIVE`

**OrganizationStatus** — estado de la organización:

* `ACTIVE`
* `SUSPENDED`

**ContactStatus** — estado del contacto externo:

* `ACTIVE` — contacto activo sin compras registradas
* `CUSTOMER` — realizó al menos una compra
* `BLOCKED` — bloqueado por la organización

---

## Value Objects

Los value objects son objetos inmutables que representan conceptos del dominio.

### core/value_objects/identifiers.py

Todos los identificadores son `@dataclass(frozen=True)` que envuelven un `uuid.UUID`.

Identificadores requeridos:

* `OrganizationId`
* `ContactId`
* `InternalUserId`
* `AgentId`
* `OpportunityId`
* `ConversationId`
* `MessageId`

Cada identificador deberá exponer exactamente dos métodos de clase:

* `generate() -> Self` — crea un nuevo UUID aleatorio
* `from_string(value: str) -> Self` — parsea un string existente

El propósito de usar tipos distintos por entidad es que MyPy detecte en tiempo de análisis si se pasa un `AgentId` donde se espera un `OpportunityId`.

No utilizar `uuid.UUID` directamente como tipo en las firmas de métodos del dominio.

---

## Entidades

Todas las entidades son `@dataclass`.

No son frozen porque representan objetos cuyo estado cambia durante su ciclo de vida.

Todos los campos `datetime` deberán almacenarse en UTC.

### core/entities/organization.py

**Organization**:

| Campo | Tipo |
|---|---|
| `id` | `OrganizationId` |
| `name` | `str` |
| `slug` | `str` |
| `timezone` | `str` (IANA, ej. "America/Bogota") |
| `language` | `str` (ISO 639-1, ej. "es") |
| `status` | `OrganizationStatus` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

### core/entities/contact.py

**Contact** — persona que inicia una conversación:

| Campo | Tipo |
|---|---|
| `id` | `ContactId` |
| `organization_id` | `OrganizationId` |
| `channel_type` | `ChannelType` |
| `external_id` | `str` |
| `display_name` | `str` |
| `status` | `ContactStatus` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

`external_id` es el identificador del contacto en el canal de origen (por ejemplo, el `chat_id` de Telegram).

La combinación `external_id + channel_type + organization_id` identifica unívocamente a un contacto.

### core/entities/internal_user.py

**InternalUser** — empleado que utiliza el Dashboard:

| Campo | Tipo |
|---|---|
| `id` | `InternalUserId` |
| `organization_id` | `OrganizationId` |
| `name` | `str` |
| `email` | `str` |
| `role` | `InternalUserRole` |
| `status` | `InternalUserStatus` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

### core/entities/agent.py

**Agent** — identidad del AI Assistant:

| Campo | Tipo |
|---|---|
| `id` | `AgentId` |
| `organization_id` | `OrganizationId` |
| `name` | `str` |
| `description` | `str` |
| `status` | `AgentStatus` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

La configuración completa del Agent (modelo, temperatura, prompt, herramientas, estrategia de memoria) se definirá en una especificación posterior dedicada al Agent Configuration System.

### core/entities/opportunity.py

**Opportunity** — aggregate root del dominio comercial:

| Campo | Tipo |
|---|---|
| `id` | `OpportunityId` |
| `organization_id` | `OrganizationId` |
| `contact_id` | `ContactId` |
| `agent_id` | `AgentId` |
| `attention_mode` | `AttentionMode` |
| `assigned_advisor_id` | `InternalUserId \| None` |
| `status` | `OpportunityStatus` |
| `channel_type` | `ChannelType` |
| `started_at` | `datetime` |
| `last_activity_at` | `datetime` |
| `closed_at` | `datetime \| None` |

`assigned_advisor_id` solo tendrá valor cuando `attention_mode` sea `HUMAN`.

La Opportunity deberá exponer los siguientes métodos de dominio que encapsulan las reglas del negocio:

**`assign_to_advisor(advisor_id: InternalUserId) -> None`**

Establece `attention_mode = HUMAN` y registra el Advisor responsable.

**`return_to_ai() -> None`**

Establece `attention_mode = AI` y limpia `assigned_advisor_id`.

**`transition_to(new_status: OpportunityStatus) -> None`**

Cambia el estado comercial. Deberá lanzar `InvalidStatusTransitionError` si la transición no es válida.

Transiciones permitidas:

* `NEW` → `QUALIFIED`, `LOST`, `CLOSED`
* `QUALIFIED` → `WAITING_FOR_ADVISOR`, `QUOTATION_PENDING`, `LOST`, `CLOSED`
* `WAITING_FOR_ADVISOR` → `QUOTATION_PENDING`, `QUALIFIED`, `LOST`, `CLOSED`
* `QUOTATION_PENDING` → `QUOTATION_SENT`, `LOST`, `CLOSED`
* `QUOTATION_SENT` → `FOLLOW_UP_PENDING`, `WON`, `LOST`, `CLOSED`
* `FOLLOW_UP_PENDING` → `QUOTATION_SENT`, `WON`, `LOST`, `CLOSED`
* `WON` → `CLOSED`
* `LOST` → `CLOSED`
* `CLOSED` → ninguna

**`record_activity() -> None`**

Actualiza `last_activity_at` a la fecha y hora actual en UTC.

### core/entities/conversation.py

**Conversation** — historial de comunicación de una Opportunity:

| Campo | Tipo |
|---|---|
| `id` | `ConversationId` |
| `opportunity_id` | `OpportunityId` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

Una Opportunity tiene exactamente una Conversation activa.

La Conversation es el contenedor que agrupa todos los mensajes.

### core/entities/message.py

**Message** — unidad mínima de comunicación:

| Campo | Tipo |
|---|---|
| `id` | `MessageId` |
| `conversation_id` | `ConversationId` |
| `role` | `MessageRole` |
| `content_type` | `MessageContentType` |
| `content` | `str` |
| `provider_message_id` | `str \| None` |
| `metadata` | `dict[str, Any]` |
| `created_at` | `datetime` |

`provider_message_id` es el identificador original del mensaje en el canal de origen (Telegram, WhatsApp, etc.).

`metadata` almacena información específica del canal que no forma parte del dominio. Nunca deberá consultarse con lógica de negocio.

---

## Eventos de dominio

Los eventos representan hechos que ocurrieron en el dominio.

Son `@dataclass(frozen=True)` porque son inmutables por definición.

Todos tienen un campo `occurred_at: datetime`.

### core/events/opportunity.py

**OpportunityCreated**:
* `opportunity_id: OpportunityId`
* `contact_id: ContactId`
* `channel_type: ChannelType`
* `occurred_at: datetime`

**OpportunityStatusChanged**:
* `opportunity_id: OpportunityId`
* `previous_status: OpportunityStatus`
* `new_status: OpportunityStatus`
* `occurred_at: datetime`

**AttentionModeChanged**:
* `opportunity_id: OpportunityId`
* `previous_mode: AttentionMode`
* `new_mode: AttentionMode`
* `assigned_advisor_id: InternalUserId | None`
* `occurred_at: datetime`

**MessageReceived**:
* `message_id: MessageId`
* `conversation_id: ConversationId`
* `opportunity_id: OpportunityId`
* `occurred_at: datetime`

**MessageSent**:
* `message_id: MessageId`
* `conversation_id: ConversationId`
* `opportunity_id: OpportunityId`
* `occurred_at: datetime`

**ConversationStarted**:
* `conversation_id: ConversationId`
* `opportunity_id: OpportunityId`
* `occurred_at: datetime`

Los eventos quedan definidos en esta especificación.

Su despacho y consumo se implementarán en especificaciones posteriores.

---

## Interfaces (Ports)

Las interfaces son contratos que el `core/` define y que `infrastructure/` implementa.

Todas usan `typing.Protocol`.

Las implementaciones en `infrastructure/` satisfacen estas interfaces sin necesidad de importar nada de `core/interfaces/`.

Todos los métodos de repositorio son `async`.

### core/interfaces/repositories.py

**OpportunityRepository**:

* `get_by_id(id: OpportunityId) -> Opportunity | None`
* `get_active_by_contact(contact_id: ContactId, channel_type: ChannelType) -> Opportunity | None`
* `save(opportunity: Opportunity) -> None`
* `list_open_by_organization(organization_id: OrganizationId) -> list[Opportunity]`

**ConversationRepository**:

* `get_by_id(id: ConversationId) -> Conversation | None`
* `get_by_opportunity(opportunity_id: OpportunityId) -> Conversation | None`
* `save(conversation: Conversation) -> None`

**MessageRepository**:

* `get_by_id(id: MessageId) -> Message | None`
* `list_by_conversation(conversation_id: ConversationId, limit: int) -> list[Message]`
* `save(message: Message) -> None`

**ContactRepository**:

* `get_by_id(id: ContactId) -> Contact | None`
* `get_by_external_id(external_id: str, channel_type: ChannelType, organization_id: OrganizationId) -> Contact | None`
* `save(contact: Contact) -> None`

**AgentRepository**:

* `get_by_id(id: AgentId) -> Agent | None`
* `get_default_by_organization(organization_id: OrganizationId) -> Agent | None`
* `save(agent: Agent) -> None`

**OrganizationRepository**:

* `get_by_id(id: OrganizationId) -> Organization | None`
* `get_by_slug(slug: str) -> Organization | None`

**InternalUserRepository**:

* `get_by_id(id: InternalUserId) -> InternalUser | None`
* `list_advisors_by_organization(organization_id: OrganizationId) -> list[InternalUser]`

**UnitOfWork**:

Coordina múltiples repositorios dentro de una única transacción de base de datos.

Deberá exponer cada repositorio como atributo de instancia:

* `opportunities: OpportunityRepository`
* `conversations: ConversationRepository`
* `messages: MessageRepository`
* `contacts: ContactRepository`
* `agents: AgentRepository`
* `organizations: OrganizationRepository`
* `internal_users: InternalUserRepository`

Y los métodos de transacción:

* `async commit() -> None`
* `async rollback() -> None`
* `async __aenter__() -> UnitOfWork`
* `async __aexit__(...) -> None`

Los servicios de aplicación siempre usarán `UnitOfWork` como context manager. Nunca administrarán transacciones directamente.

### core/interfaces/providers.py

**ChannelProvider**:

* `async send(message: Message, opportunity: Opportunity) -> None`
* `async health() -> bool`

**AIProvider**:

* `async generate(messages: list[Message], agent_id: AgentId) -> str`
* `async health() -> bool`

---

## Excepciones del dominio

### core/exceptions/domain.py

Jerarquía:

```
DomainError(Exception)
├── OpportunityNotFoundError
├── OpportunityAlreadyClosedError
├── InvalidStatusTransitionError
│       (campos: current_status, attempted_status)
├── ContactNotFoundError
├── AgentNotFoundError
└── OrganizationNotFoundError
```

`DomainError` es la clase base de todas las excepciones del dominio.

Las capas superiores (`app/`, `modules/`) capturarán `DomainError` para convertirla en respuestas HTTP apropiadas.

`InvalidStatusTransitionError` deberá incluir en su mensaje tanto el estado actual como el intentado, para facilitar el diagnóstico.

---

## Lo que NO debe hacerse

Durante esta especificación queda explícitamente prohibido:

* crear modelos SQLAlchemy — pertenecen a la especificación 003
* crear endpoints FastAPI — pertenecen a especificaciones posteriores
* implementar `ChannelProvider` o `AIProvider` — solo se definen las interfaces
* implementar ningún repositorio — solo se definen las interfaces
* crear servicios de aplicación — solo el dominio puro
* importar ningún framework externo dentro de `core/`

---

## Definición de terminado

La tarea se considerará terminada cuando:

* todos los archivos listados en la estructura existan en `core/`;
* todas las entidades estén definidas como `@dataclass`;
* todos los identificadores existan como value objects tipados;
* todos los enums contengan exactamente los valores definidos en este documento;
* todas las interfaces estén definidas como `typing.Protocol`;
* la Opportunity exponga los métodos de dominio con las transiciones de estado documentadas;
* `ruff check .` pase sin errores desde `backend/`;
* `mypy app core` pase sin errores desde `backend/`;
* ningún archivo dentro de `core/` importe SQLAlchemy, Pydantic, FastAPI ni ningún módulo de `infrastructure/`.

---

## Principio fundamental

`core/` es el corazón del sistema.

Su única dependencia es el lenguaje Python.

Si en el futuro se reemplaza FastAPI por otro framework, SQLite por PostgreSQL, Telegram por WhatsApp, o cualquier otra tecnología, el `core/` no deberá cambiar.

Esa independencia es la garantía de que la plataforma puede evolucionar sin reescrituras.

