# PROYECTO

Vas a construir una plataforma profesional de agentes conversacionales impulsados por Inteligencia Artificial.

NO estás construyendo un bot.

NO estás construyendo una integración con Telegram.

NO estás construyendo una integración con WhatsApp.

Estás construyendo una plataforma capaz de administrar conversaciones provenientes de múltiples canales de mensajería mediante una arquitectura desacoplada, modular y escalable.

Telegram será el primer canal implementado únicamente para acelerar el desarrollo y las pruebas.

Posteriormente deberán poder incorporarse nuevos canales como:

- WhatsApp Cloud API
- Messenger
- Instagram
- Discord
- Microsoft Teams
- Slack

sin modificar la lógica principal del sistema.

---

# OBJETIVO GENERAL

Construir una plataforma que permita:

- recibir conversaciones desde múltiples canales
- responder automáticamente mediante Inteligencia Artificial
- permitir intervención humana
- administrar historial
- administrar múltiples agentes
- administrar múltiples proveedores de IA
- incorporar herramientas externas
- incorporar memoria conversacional
- escalar fácilmente hacia nuevos canales

La arquitectura debe permitir agregar nuevas capacidades sin modificar el Core del sistema.

---

# FILOSOFÍA DEL PROYECTO

Este proyecto debe escribirse con calidad empresarial.

Todo el código debe asumir que será mantenido durante muchos años.

Cada decisión debe priorizar:

1. mantenibilidad
2. simplicidad
3. escalabilidad
4. claridad
5. desacoplamiento

Nunca debe priorizarse escribir menos líneas de código sobre una buena arquitectura.

---

# ARQUITECTURA GENERAL

La aplicación estará dividida en dos proyectos completamente independientes.

Frontend

Dashboard administrativo.

Backend

Motor completo del agente conversacional.

Ambos proyectos únicamente se comunicarán mediante una API REST.

El frontend jamás accederá directamente a la base de datos.

El frontend jamás contendrá lógica del negocio.

Toda la lógica residirá exclusivamente en el backend.

---

# TECNOLOGÍA

## Backend

Python 3.12+

FastAPI

SQLAlchemy 2

Alembic

Pydantic v2

HTTPX

OpenAI SDK compatible con OpenRouter

SQLite para desarrollo

PostgreSQL para producción

---

## Frontend

Next.js 16

React 19

TypeScript

TailwindCSS 4

El frontend tendrá únicamente responsabilidades de presentación.

---

# ESTILO DE ARQUITECTURA

Toda la solución deberá seguir una Arquitectura Hexagonal (Ports & Adapters).

La lógica del negocio nunca dependerá de:

- Telegram
- WhatsApp
- OpenRouter
- SQLite
- PostgreSQL
- FastAPI

Todos estos componentes deberán implementarse como adaptadores externos.

---

# PRINCIPIOS OBLIGATORIOS

El proyecto deberá seguir estrictamente los principios:

SOLID

Clean Code

DRY

KISS

YAGNI

High Cohesion

Low Coupling

Dependency Inversion

Composition over Inheritance

Explicit is Better than Implicit

Todos los módulos deberán respetar estos principios.

---

# RESPONSABILIDAD ÚNICA

Cada archivo deberá tener una única responsabilidad.

No crear archivos gigantes.

No mezclar múltiples responsabilidades en una misma clase.

No escribir funciones excesivamente largas.

No crear clases "God Object".

No usar emoticones ni caracteres especiales, ni en el código ni en documentación.

No usar guiones ("-") en la documenatción general, decada clase o función.

---

# API FIRST

Toda funcionalidad deberá exponerse mediante la API del backend.

El Dashboard será simplemente un consumidor de dicha API.

Toda nueva funcionalidad deberá implementarse primero en el backend y posteriormente consumirse desde el frontend.

---

# MODULARIDAD

La plataforma estará dividida en módulos completamente independientes.

Ejemplos:

Authentication

Channels

AI

Memory

Prompts

Tools

Dashboard

Database

Configuration

Repositories

Services

Cada módulo deberá poder evolucionar independientemente.

---

# DESACOPLAMIENTO

El Core jamás conocerá:

Telegram

WhatsApp

OpenRouter

SQLite

PostgreSQL

FastAPI

HTTPX

Todos estos componentes deberán implementarse mediante interfaces.

---

# PRINCIPIO DE INVERSIÓN DE DEPENDENCIAS

La lógica del negocio únicamente dependerá de abstracciones.

Nunca dependerá de implementaciones concretas.

Todo acceso a servicios externos deberá realizarse mediante Providers.

Ejemplos:

ChannelProvider

AIProvider

MemoryProvider

ToolProvider

StorageProvider

Cada implementación concreta deberá respetar exactamente la misma interfaz.

---

# CORE DEL SISTEMA

El Core será completamente independiente de cualquier tecnología.

El Core únicamente conocerá entidades del dominio.

Ejemplos:

Opportunity

Message

Agent

Tool

Memory

Prompt

Provider

Channel

Nunca conocerá Telegram.

Nunca conocerá WhatsApp.

Nunca conocerá OpenRouter.

Nunca conocerá FastAPI.

---

# FLUJO GENERAL

El flujo completo del sistema será:

Usuario

↓

Canal de mensajería

↓

Provider del canal

↓

Opportunity Engine

↓

Memory Engine

↓

Prompt Engine

↓

Tool Engine

↓

AI Provider

↓

Provider del canal

↓

Usuario

El motor de conversación nunca deberá conocer el canal desde el cual provino el mensaje.

---

# PRIMERA IMPLEMENTACIÓN

La primera versión implementará únicamente Telegram.

Toda la arquitectura deberá quedar preparada para incorporar posteriormente:

WhatsApp Cloud API

Messenger

Instagram

Discord

Slack

sin modificar el Core.

Agregar un nuevo canal deberá consistir únicamente en crear un nuevo Provider.

---

# CÓDIGO PREPARADO PARA PRODUCCIÓN

No escribir código temporal.

No dejar funciones incompletas.

No dejar TODOs.

No dejar código comentado.

No dejar implementaciones parciales.

No escribir soluciones rápidas que comprometan la arquitectura.

Todo el código deberá considerarse listo para producción desde la primera versión.

---

# REGLAS OBLIGATORIAS

Está prohibido:

- escribir lógica específica del canal fuera de su Provider

- acceder directamente a Telegram desde el Dashboard

- acceder directamente a WhatsApp desde el Dashboard

- acceder directamente a la base de datos desde el frontend

- duplicar lógica entre Providers

- utilizar condicionales para distinguir canales dentro del Core

- acoplar la lógica del negocio a una tecnología específica

Toda diferencia entre canales deberá resolverse mediante polimorfismo e implementación de interfaces.

---

# OBJETIVO FINAL

Al finalizar el proyecto deberá existir una plataforma profesional de agentes conversacionales, preparada para evolucionar durante muchos años, donde la incorporación de nuevos canales, nuevos modelos de IA, nuevas herramientas o nuevas memorias requiera únicamente agregar nuevos adaptadores, sin modificar la lógica principal del sistema.

# ESTRUCTURA GENERAL DEL PROYECTO

El proyecto estará dividido en dos aplicaciones completamente independientes.

```
Opportunity-platform/

│

├── backend/

├── frontend/

├── docs/

├── scripts/

├── docker-compose.yml

├── .env.example

├── .gitignore

└── README.md
```

El backend contendrá toda la lógica del negocio.

El frontend contendrá únicamente la interfaz administrativa.

No deberá existir ninguna lógica del negocio en el frontend.

---

# BACKEND

El backend utilizará Python 3.12+ y FastAPI.

Su estructura será la siguiente.

```
backend/

│

├── app/

│

├── core/

│

├── modules/

│

├── infrastructure/

│

├── tests/

│

├── migrations/

│

├── requirements.txt

│

├── pyproject.toml

│

└── main.py
```

Cada carpeta tiene una responsabilidad específica.

---

# APP

```
app/

main.py

config.py

dependencies.py

logging.py

exceptions.py

security.py

lifecycle.py
```

Responsabilidades:

- inicialización de FastAPI
- configuración global
- middlewares
- manejo de errores
- ciclo de vida
- inyección de dependencias

No debe existir lógica del negocio aquí.

---

# CORE

El Core representa el dominio.

Nunca conocerá tecnologías.

Nunca conocerá proveedores externos.

Nunca conocerá Telegram.

Nunca conocerá OpenRouter.

Nunca conocerá FastAPI.

El Core únicamente conocerá reglas del negocio.

```
core/

entities/

interfaces/

value_objects/

exceptions/

events/

constants/

enums/
```

---

# ENTITIES

Representan el dominio.

Ejemplos:

Opportunity

Message

Agent

Channel

Memory

Prompt

Tool

User

Configuration

Las entidades no deberán depender de SQLAlchemy.

Las entidades no deberán depender de Pydantic.

Las entidades deberán ser completamente independientes.

---

# VALUE OBJECTS

Representan objetos inmutables del dominio.

Ejemplos:

PhoneNumber

ChatId

MessageId

OpportunityId

AgentId

Temperature

ModelName

Role

Mode

---

# INTERFACES

El Core únicamente conoce interfaces.

Nunca implementaciones.

Ejemplos:

ChannelProvider

AIProvider

MemoryProvider

StorageProvider

OpportunityRepository

PromptRepository

ToolProvider

KnowledgeProvider

EmbeddingProvider

VectorStoreProvider

---

# EVENTS

Preparar el sistema para eventos internos.

Ejemplos:

OpportunityCreated

MessageReceived

MessageSent

OpportunityClosed

ToolExecuted

AgentChanged

Aunque inicialmente algunos eventos no se utilicen, la arquitectura debe permitir incorporarlos fácilmente.

---

# MODULES

Toda funcionalidad del sistema estará organizada por dominios.

Nunca por tipo de archivo.

```
modules/

agents/

channels/

Opportunitys/

dashboard/

knowledge/

llm/

memory/

prompts/

tools/

users/

configuration/
```

Cada módulo será completamente independiente.

---

# ESTRUCTURA DE UN MÓDULO

Todos los módulos deberán seguir exactamente la misma organización.

Ejemplo:

```
modules/Opportunitys/

api/

services/

repositories/

schemas/

models/

domain/

validators/

exceptions/

tests/
```

---

## api

Expone los endpoints REST.

No contiene lógica del negocio.

Únicamente valida datos y llama servicios.

---

## services

Implementa casos de uso.

Toda la lógica reside aquí.

Cada servicio deberá tener una única responsabilidad.

---

## repositories

Acceso a datos.

Nunca contener lógica del negocio.

Toda consulta SQL deberá vivir aquí.

---

## schemas

Modelos Pydantic.

Separados completamente de SQLAlchemy.

Nunca reutilizar modelos ORM como modelos de entrada o salida.

---

## models

Modelos SQLAlchemy.

Persistencia únicamente.

No contienen lógica.

---

## validators

Validaciones específicas del módulo.

---

## tests

Pruebas unitarias del módulo.

---

# INFRASTRUCTURE

Representa todas las implementaciones concretas.

```
infrastructure/

database/

channels/

ai/

memory/

storage/

tools/

logging/

cache/

repositories/
```

Todo componente externo vive aquí.

Nunca dentro del Core.

---

# DATABASE

```
database/

engine.py

session.py

base.py

migrations.py

```

Toda configuración de SQLAlchemy vive aquí.

---

# CHANNELS

Cada canal implementará exactamente la misma interfaz.

```
channels/

telegram/

whatsapp/

messenger/

discord/

instagram/

base.py
```

Inicialmente solamente existirá:

```
telegram/
```

Los demás módulos quedarán preparados.

---

# AI

Los modelos de IA también deberán implementarse mediante Providers.

```
ai/

openrouter/

openai/

anthropic/

gemini/

ollama/

base.py
```

El sistema nunca deberá depender de un proveedor específico.

Cambiar el modelo deberá requerir únicamente modificar la configuración.

---

# MEMORY

La memoria también deberá ser intercambiable.

```
memory/

sqlite/

postgres/

redis/

base.py
```

La primera versión utilizará SQLite.

La arquitectura deberá permitir migrar fácilmente a PostgreSQL.

---

# TOOLS

Todas las herramientas externas vivirán aquí.

```
tools/

calculator/

calendar/

crm/

email/

inventory/

documents/

knowledge/

```

Inicialmente muchas estarán vacías.

La arquitectura deberá quedar preparada.

---

# TESTS

Toda funcionalidad importante deberá contar con pruebas.

```
tests/

unit/

integration/

e2e/
```

No mezclar pruebas con código productivo.

---

# FRONTEND

El frontend será únicamente un Dashboard.

Nunca contendrá lógica del negocio.

```
frontend/

app/

components/

hooks/

services/

types/

styles/

public/
```

---

# COMPONENTES

Todos los componentes React deberán ser pequeños.

Un componente debe tener una única responsabilidad.

Si supera aproximadamente 250 líneas deberá dividirse.

---

# SERVICES

El frontend accederá al backend exclusivamente mediante una capa de servicios.

Nunca realizar llamadas fetch directamente desde los componentes.

Ejemplo:

```
services/

Opportunity.service.ts

agent.service.ts

configuration.service.ts

channel.service.ts

message.service.ts
```

---

# CONFIGURACIÓN

Toda configuración deberá centralizarse.

Nunca utilizar variables de entorno directamente desde múltiples archivos.

Crear un único módulo de configuración.

---

# VARIABLES DE ENTORNO

Todo acceso a variables de entorno deberá validarse al iniciar la aplicación.

Si falta alguna variable obligatoria, el backend no deberá iniciar.

Nunca descubrir errores de configuración durante la ejecución.

---

# LOGGING

Todo el sistema deberá utilizar logging estructurado.

No utilizar print().

Registrar:

- errores

- advertencias

- llamadas a IA

- ejecución de herramientas

- mensajes recibidos

- mensajes enviados

- tiempos de respuesta

- consumo de tokens

---

# REGLA GENERAL

Cada carpeta deberá tener una única responsabilidad.

Cada módulo deberá poder evolucionar independientemente.

La incorporación de nuevas funcionalidades nunca deberá requerir reorganizar la estructura del proyecto.

La estructura definida en este documento deberá mantenerse durante toda la vida del proyecto.

# EL CORE DEL SISTEMA

El Core representa el corazón de toda la plataforma.

Toda la lógica del negocio deberá residir aquí.

El Core nunca deberá depender de:

- FastAPI
- SQLAlchemy
- Telegram
- WhatsApp
- OpenRouter
- OpenAI
- Anthropic
- Gemini
- SQLite
- PostgreSQL
- Redis

El Core únicamente conoce reglas del negocio.

---

# RESPONSABILIDADES DEL CORE

El Core será responsable de:

- administrar conversaciones

- administrar agentes

- administrar memoria conversacional

- decidir cuándo responder

- decidir cuándo utilizar herramientas

- construir el contexto del LLM

- mantener el historial

- controlar el modo IA/HUMANO

- coordinar todo el flujo conversacional

El Core jamás enviará mensajes directamente.

El Core jamás realizará consultas HTTP.

El Core jamás ejecutará SQL.

---

# ARQUITECTURA INTERNA

El Core estará dividido en los siguientes motores.

Opportunity Engine

↓

Agent Engine

↓

Memory Engine

↓

Prompt Engine

↓

Tool Engine

↓

AI Engine

Cada motor tendrá una única responsabilidad.

---

# Opportunity ENGINE

Es el orquestador principal.

Toda conversación ingresará primero aquí.

Responsabilidades:

- crear conversaciones

- recuperar conversaciones existentes

- registrar mensajes

- decidir si responde IA o humano

- construir el contexto

- solicitar respuesta al AI Engine

- registrar la respuesta

- solicitar el envío al Channel Provider

El Opportunity Engine nunca conocerá Telegram.

Nunca conocerá WhatsApp.

---

# AGENT ENGINE

Administra los agentes.

Cada conversación siempre pertenece a un único agente.

El agente define:

- personalidad

- idioma

- modelo

- temperatura

- herramientas disponibles

- memoria disponible

- prompt base

En futuras versiones podrán existir múltiples agentes.

---

# MEMORY ENGINE

Su responsabilidad consiste únicamente en construir el contexto conversacional.

No consulta directamente bases de datos.

No consulta directamente embeddings.

Siempre utiliza un MemoryProvider.

Debe soportar:

Memoria reciente

Memoria resumida

Memoria permanente

Memoria semántica

Aunque inicialmente sólo se implemente memoria reciente.

---

# PROMPT ENGINE

Construye el prompt final.

Debe combinar:

Prompt del sistema

+

Configuración del agente

+

Memoria

+

Mensaje actual

+

Resultado de herramientas

+

Contexto adicional

Nunca construir prompts manualmente desde múltiples lugares.

Todo prompt deberá construirse aquí.

---

# TOOL ENGINE

Administra todas las herramientas disponibles.

Responsabilidades:

- descubrir herramientas

- validar parámetros

- ejecutar herramientas

- devolver resultados

El Opportunity Engine nunca ejecutará herramientas directamente.

Siempre utilizará Tool Engine.

---

# AI ENGINE

Es el único responsable de interactuar con el proveedor de IA.

Nunca construir prompts.

Nunca consultar memoria.

Nunca ejecutar herramientas.

Recibe un prompt completamente construido.

Devuelve una respuesta.

Nada más.

---

# PROVIDERS

Todo componente externo deberá implementarse mediante Providers.

El Core únicamente conoce las interfaces.

Nunca las implementaciones.

---

# CHANNEL PROVIDER

Responsabilidad:

Enviar y recibir mensajes.

La interfaz mínima será:

receive()

send()

verify()

health()

normalize()

Cada canal implementará exactamente esta interfaz.

Ejemplos:

TelegramProvider

WhatsAppProvider

MessengerProvider

DiscordProvider

---

# AI PROVIDER

Responsabilidad:

Generar respuestas utilizando un modelo LLM.

Métodos mínimos:

generate()

stream()

health()

list_models()

Implementaciones:

OpenRouter

OpenAI

Anthropic

Gemini

Ollama

---

# MEMORY PROVIDER

Responsabilidad:

Persistir memoria.

Métodos mínimos:

store()

retrieve()

delete()

summarize()

Implementaciones futuras:

SQLiteMemory

PostgresMemory

RedisMemory

VectorMemory

---

# STORAGE PROVIDER

Responsabilidad:

Persistencia de archivos.

Implementaciones:

Local

S3

Cloud Storage

No deberá utilizarse directamente desde el Core.

---

# TOOL PROVIDER

Responsabilidad:

Registrar herramientas disponibles.

Métodos:

register()

execute()

validate()

list()

---

# KNOWLEDGE PROVIDER

Responsabilidad:

Consultar conocimiento externo.

Ejemplos:

PDF

Base documental

FAQ

Manual

Wiki

Vector Database

El Core nunca consultará documentos directamente.

---

# ENTIDADES DEL DOMINIO

Las entidades principales serán:

Opportunity

Message

Agent

Channel

Tool

Knowledge

Memory

Prompt

Attachment

Configuration

User

---

# MESSAGE

Todo mensaje del sistema deberá utilizar exactamente la misma estructura.

Nunca crear estructuras distintas para Telegram y WhatsApp.

Ejemplo conceptual:

Message

id

Opportunity_id

role

content

created_at

metadata

channel_message_id

attachments

---

# Opportunity

Representa una conversación independientemente del canal.

Debe contener:

id

channel

external_user_id

display_name

mode

agent_id

status

created_at

updated_at

Nunca almacenar información específica de Telegram.

Nunca almacenar información específica de WhatsApp.

---

# AGENT

Representa un asistente virtual.

Debe contener:

id

name

description

model

temperature

system_prompt

enabled_tools

memory_strategy

language

Cada conversación utilizará un único agente.

---

# CONFIGURATION

Toda configuración del sistema deberá almacenarse mediante una entidad específica.

Nunca utilizar constantes distribuidas por el proyecto.

---

# FLUJO COMPLETO

El flujo oficial será:

Usuario

↓

Channel Provider

↓

Opportunity Engine

↓

Memory Engine

↓

Prompt Engine

↓

Tool Engine

↓

AI Engine

↓

Channel Provider

↓

Usuario

Todas las conversaciones deberán seguir exactamente este flujo.

No deberán existir caminos alternativos.

---

# REGLA GENERAL

El Core nunca dependerá de infraestructura.

La infraestructura siempre dependerá del Core.

Toda dependencia deberá apuntar hacia el dominio.

Nunca en sentido contrario.

# EL AGENTE

El concepto principal de toda la plataforma es el Agente.

Toda conversación pertenece exactamente a un Agente.

El Agente representa una entidad inteligente capaz de tomar decisiones, utilizar herramientas, consultar memoria y responder al usuario.

El usuario nunca interactúa directamente con el modelo LLM.

Siempre interactúa con un Agente.

---

# FILOSOFÍA

El modelo LLM NO es el agente.

El LLM es únicamente uno de los componentes utilizados por el Agente.

El Agente controla completamente la conversación.

El LLM únicamente genera texto.

---

# AGENT RUNTIME

Cada mensaje recibido será procesado por un Agent Runtime.

El Runtime será el verdadero orquestador del sistema.

Su responsabilidad será coordinar todos los componentes necesarios para producir una respuesta.

---

# RESPONSABILIDADES DEL RUNTIME

El Runtime deberá:

• cargar la configuración del agente

• recuperar la conversación

• recuperar la memoria

• recuperar conocimiento

• decidir si ejecutar herramientas

• construir el contexto

• invocar el proveedor de IA

• validar la respuesta

• almacenar el resultado

• solicitar el envío del mensaje

Toda la lógica conversacional deberá vivir aquí.

---

# CICLO DE VIDA DE UN MENSAJE

Todo mensaje deberá seguir exactamente este flujo.

Mensaje recibido

↓

Identificar canal

↓

Normalizar mensaje

↓

Identificar conversación

↓

Identificar agente

↓

Cargar configuración

↓

Recuperar memoria

↓

Recuperar conocimiento

↓

Construir contexto

↓

Evaluar herramientas

↓

Ejecutar herramientas (si aplica)

↓

Actualizar contexto

↓

Invocar proveedor IA

↓

Validar respuesta

↓

Persistir respuesta

↓

Enviar respuesta

↓

Registrar métricas

No deberán existir flujos alternativos.

---

# AGENT CONFIGURATION

Cada Agente deberá poseer una configuración independiente.

Como mínimo:

id

nombre

descripción

idioma

modelo

temperatura

prompt base

modo de memoria

herramientas habilitadas

proveedor IA

estado

mensaje de bienvenida

mensaje de transferencia

horario de atención

---

# AGENT STATE

Todo agente deberá encontrarse en uno de los siguientes estados.

ACTIVE

Recibe conversaciones normalmente.

PAUSED

No responde automáticamente.

DISABLED

No acepta nuevas conversaciones.

MAINTENANCE

Responde indicando que se encuentra temporalmente fuera de servicio.

---

# AGENT CAPABILITIES

Cada agente podrá habilitar o deshabilitar capacidades.

Ejemplos:

Uso de memoria

Uso de herramientas

Consulta documental

Transferencia a humano

Streaming

Generación de archivos

Respuestas largas

Cada capacidad deberá poder configurarse independientemente.

---

# AGENT PROFILE

El comportamiento del agente no deberá codificarse en Python.

Toda personalidad deberá definirse mediante configuración.

Ejemplos:

Nombre

Rol

Objetivo

Personalidad

Idioma

Nivel de formalidad

Restricciones

Políticas

Todos estos parámetros deberán formar parte del Prompt del Sistema.

---

# PROMPT DEL SISTEMA

Cada agente tendrá su propio Prompt.

Nunca deberá existir un único system_prompt.py.

El Prompt deberá almacenarse como configuración del Agente.

En futuras versiones deberá poder editarse desde el Dashboard.

---

# TEMPERATURA

Cada agente podrá utilizar una temperatura distinta.

La temperatura nunca deberá encontrarse fija en el código.

---

# MODELO

Cada agente podrá utilizar un modelo diferente.

Ejemplos:

GPT-4.1

Claude

Gemini

Llama

Mistral

Cambiar de modelo nunca deberá requerir modificar código.

---

# MEMORIA

Cada agente podrá utilizar una estrategia diferente.

Ejemplos:

Sin memoria

Memoria reciente

Resumen automático

Memoria semántica

RAG

La estrategia deberá configurarse por agente.

---

# HERRAMIENTAS

Cada agente decidirá qué herramientas puede utilizar.

Ejemplo:

Agente Ventas

• consultar inventario

• calcular precio

• generar cotización

Agente Soporte

• consultar manuales

• buscar tickets

• consultar garantía

Cada herramienta deberá declararse explícitamente.

---

# TRANSFERENCIA A HUMANO

El Runtime deberá soportar transferencia a un operador humano.

Cuando una conversación se encuentre en modo HUMAN:

El Runtime no deberá generar respuestas.

Únicamente deberá registrar los mensajes.

El operador responderá desde el Dashboard o desde la app nativa.

---

# MÉTRICAS

Cada ejecución del Runtime deberá registrar métricas.

Como mínimo:

hora inicio

hora fin

duración

modelo utilizado

tokens entrada

tokens salida

herramientas ejecutadas

errores

canal

agente

usuario

Estas métricas permitirán auditoría y optimización futura.

---

# OBSERVABILIDAD

Toda ejecución deberá poder reconstruirse posteriormente.

El sistema deberá registrar cada paso importante.

Ejemplos:

Mensaje recibido

Agente seleccionado

Prompt construido

Herramientas ejecutadas

Tiempo de respuesta

Proveedor IA

Respuesta enviada

Error producido

Nunca registrar información sensible.

---

# MULTIAGENTE

La arquitectura deberá permitir que una conversación sea transferida entre agentes.

Ejemplo:

Recepción

↓

Ventas

↓

Soporte

↓

Facturación

La conversación deberá conservar todo su historial.

---

# ESCALABILIDAD

Agregar un nuevo agente nunca deberá requerir escribir código Python.

Deberá consistir únicamente en crear una nueva configuración.

Toda la lógica deberá reutilizar exactamente el mismo Runtime.

---

# PRINCIPIO FUNDAMENTAL

El Runtime es único.

Los Agentes son configuraciones.

Nunca crear un Runtime distinto para cada Agente.

Todos los Agentes deberán compartir exactamente el mismo motor conversacional.

# AGENT DEFINITION SYSTEM (ADS)

La plataforma no deberá definir el comportamiento de los agentes mediante código Python.

Todo agente deberá definirse mediante configuración estructurada.

El Runtime será completamente genérico.

Los Agentes únicamente serán configuraciones.

---

# FILOSOFÍA

El Runtime nunca deberá contener reglas específicas de un agente.

Nunca escribir:

if agente == ventas

if agente == soporte

if agente == citas

Toda diferencia entre agentes deberá resolverse mediante configuración.

---

# ESTRUCTURA DEL ADS

Todo Agente estará compuesto por exactamente las siguientes capas.

Organization

↓

Agent

↓

Identity

↓

Policies

↓

Capabilities

↓

Memory Strategy

↓

Knowledge Strategy

↓

Prompt Builder

↓

Runtime

Cada capa tendrá una única responsabilidad.

---

# ORGANIZATION

Toda la plataforma deberá pertenecer a una Organización.

Inicialmente existirá una única Organización.

La arquitectura deberá permitir múltiples organizaciones en futuras versiones.

Una Organización podrá contener:

Agentes

Usuarios

Conocimiento

Herramientas

Configuraciones

Canales

Plantillas

Conversaciones

Toda conversación siempre pertenecerá a una Organización.

---

# AGENT

El Agente representa una configuración ejecutable.

No contiene lógica.

No contiene código.

No contiene funciones.

Únicamente configuración.

---

# IDENTITY

La Identidad define quién es el Agente.

Ejemplo:

Nombre

Descripción

Rol

Idioma

Zona horaria

Nivel de formalidad

Personalidad

Objetivo

Público objetivo

Industria

La Identidad nunca deberá contener instrucciones operativas.

---

# POLICIES

Las Policies definen el comportamiento permitido.

Ejemplos:

Puede transferir conversaciones.

Puede responder fuera del horario.

Puede utilizar herramientas.

Puede responder preguntas personales.

Puede generar archivos.

Puede acceder al conocimiento.

Puede solicitar intervención humana.

Puede utilizar memoria.

Toda regla del negocio deberá declararse aquí.

Nunca esconder reglas dentro del Prompt.

---

# CAPABILITIES

Las Capabilities representan funcionalidades disponibles.

Ejemplos:

Opportunity

Memory

Knowledge

Tools

Streaming

Voice

Images

Files

Analytics

Cada Capability podrá habilitarse o deshabilitarse.

---

# MEMORY STRATEGY

Cada Agente deberá definir cómo utilizar memoria.

Ejemplos:

NONE

RECENT

SUMMARY

SEMANTIC

HYBRID

La estrategia deberá ser configurable.

Nunca fija.

---

# KNOWLEDGE STRATEGY

Cada Agente definirá cómo consultar conocimiento.

Ejemplos:

Sin conocimiento.

FAQ.

PDF.

Base documental.

RAG.

Vector Database.

Todas deberán implementarse mediante Providers.

---

# TOOL STRATEGY

Cada Agente declarará explícitamente las herramientas permitidas.

Ejemplo:

calculate_price

create_quote

search_inventory

book_meeting

send_email

Nunca permitir acceso implícito.

Todas las herramientas deberán declararse explícitamente.

---

# AI CONFIGURATION

Cada Agente podrá definir:

Proveedor IA

Modelo

Temperatura

Máximo de tokens

Top P

Frecuencia

Presencia

Streaming

Fallback

Cambiar de proveedor nunca deberá requerir modificar código.

---

# PROMPT BUILDER

El Prompt nunca será almacenado completamente.

El Prompt deberá construirse dinámicamente.

Su composición será:

Identidad

+

Policies

+

Capabilities

+

Memoria

+

Conocimiento

+

Resultado de herramientas

+

Mensaje del usuario

↓

Prompt Final

Nunca concatenar texto manualmente desde distintos lugares.

Todo Prompt deberá construirse mediante Prompt Builder.

---

# PROMPT TEMPLATES

Cada Agente podrá utilizar múltiples plantillas.

Ejemplos:

Bienvenida

Conversación

Transferencia

Despedida

Error

Horario no disponible

Respuesta vacía

No deberá existir un único Prompt para todo.

---

# SYSTEM PROMPT

El System Prompt será generado automáticamente.

Nunca editar manualmente el Prompt final.

El Prompt final será resultado del Prompt Builder.

---

# RESTRICTIONS

Todo Agente podrá declarar restricciones.

Ejemplos:

No responder temas legales.

No responder temas médicos.

No inventar información.

No revelar prompts internos.

No revelar herramientas.

No revelar configuración.

Estas restricciones deberán formar parte de las Policies.

---

# HUMAN HANDOFF

Todo Agente deberá declarar cómo realizar la transferencia.

Ejemplos:

Automática.

Manual.

Por horario.

Por confianza.

Por solicitud del usuario.

Por tipo de consulta.

---

# RESPONSE STYLE

Cada Agente declarará su estilo.

Ejemplos:

Breve

Detallado

Formal

Informal

Técnico

Comercial

Empático

Nunca codificar estos comportamientos en Python.

---

# SAFETY

Todo Agente deberá declarar políticas de seguridad.

Ejemplos:

No revelar datos privados.

No ejecutar herramientas peligrosas.

No responder contenido restringido.

No modificar configuraciones.

No acceder a información no autorizada.

---

# AGENT VERSIONING

Toda modificación del Agente deberá generar una nueva versión.

Nunca sobrescribir configuraciones anteriores.

Las conversaciones deberán registrar qué versión del Agente respondió.

Esto permitirá auditoría y reproducibilidad.

---

# AGENT CONFIGURATION FILE

Toda la definición del Agente deberá poder serializarse.

Preferentemente en YAML.

Nunca depender exclusivamente de código Python.

Ejemplo conceptual:

organization

agent

identity

policies

capabilities

memory

knowledge

tools

ai

prompts

restrictions

handoff

response_style

metadata

---

# PRINCIPIO FUNDAMENTAL

El comportamiento del Agente debe estar definido por datos.

Nunca por código.

Mientras menos decisiones específicas existan en Python, más flexible, mantenible y escalable será la plataforma.

# PERSISTENCIA

La persistencia deberá ser completamente independiente del dominio.

El dominio nunca conocerá SQLAlchemy.

El dominio nunca conocerá SQLite.

El dominio nunca conocerá PostgreSQL.

Toda persistencia deberá realizarse mediante Repositories.

---

# MOTORES SOPORTADOS

El proyecto deberá soportar oficialmente:

Desarrollo

• SQLite

Producción

• PostgreSQL

La selección del motor deberá realizarse mediante configuración.

Nunca mediante cambios de código.

---

# SQLALCHEMY

Toda la persistencia utilizará SQLAlchemy 2.x.

Modo Declarative.

Typing completo.

Mapped[].

mapped_column().

Nunca utilizar APIs antiguas.

---

# ALEMBIC

Toda modificación del esquema deberá realizarse mediante migraciones.

Nunca modificar tablas manualmente.

Nunca ejecutar CREATE TABLE directamente desde la aplicación.

Toda evolución del esquema deberá quedar versionada.

---

# UNIT OF WORK

Toda operación de escritura deberá ejecutarse mediante un Unit of Work.

Responsabilidades:

- abrir transacción

- confirmar cambios

- rollback automático

- cerrar sesión

Los Services nunca deberán administrar transacciones manualmente.

---

# REPOSITORY PATTERN

Toda entidad del dominio deberá poseer un Repository.

Ejemplos:

OpportunityRepository

MessageRepository

AgentRepository

OrganizationRepository

KnowledgeRepository

ToolRepository

ConfigurationRepository

Nunca acceder directamente a SQLAlchemy desde los Services.

---

# RESPONSABILIDAD DE LOS REPOSITORIES

Los Repositories únicamente realizan operaciones de persistencia.

Nunca contienen reglas del negocio.

Nunca construyen prompts.

Nunca llaman modelos IA.

Nunca ejecutan herramientas.

---

# ESTRUCTURA DE LA BASE DE DATOS

El modelo deberá diseñarse para múltiples organizaciones.

Aunque inicialmente exista una sola.

---

## ORGANIZATIONS

Representa una empresa o cliente.

Campos mínimos:

id

name

slug

timezone

language

status

created_at

updated_at

---

## AGENTS

Cada Organización podrá tener múltiples Agentes.

Campos:

id

organization_id

name

description

status

configuration_version

created_at

updated_at

---

## AGENT_CONFIGURATIONS

Cada modificación genera una nueva versión.

Campos:

id

agent_id

version

configuration_yaml

created_at

Nunca sobrescribir configuraciones.

Siempre versionar.

---

## CHANNELS

Representa un canal habilitado.

Campos:

id

organization_id

provider

configuration

status

created_at

---

## OpportunityS

Toda conversación pertenece a:

una Organización

un Agente

un Canal

un Usuario externo

Campos:

id

organization_id

agent_id

channel_id

external_user_id

display_name

mode

status

started_at

last_message_at

closed_at

---

## MESSAGES

Representa todos los mensajes.

Campos:

id

Opportunity_id

role

content

provider_message_id

metadata

created_at

Nunca crear tablas distintas por canal.

---

## USERS

Usuarios internos del Dashboard.

Campos:

id

organization_id

name

email

role

status

created_at

Aunque inicialmente no exista autenticación.

La estructura deberá quedar preparada.

---

## KNOWLEDGE_BASES

Representa fuentes documentales.

Campos:

id

organization_id

name

type

provider

status

configuration

created_at

---

## DOCUMENTS

Representa documentos.

Campos:

id

knowledge_base_id

filename

checksum

mime_type

status

created_at

---

## TOOLS

Herramientas disponibles.

Campos:

id

organization_id

name

provider

configuration

status

---

## EXECUTIONS

Cada ejecución del Runtime deberá registrarse.

Campos:

id

Opportunity_id

agent_id

model

started_at

finished_at

duration_ms

prompt_tokens

completion_tokens

total_tokens

status

error

---

## AUDIT_LOG

Toda acción importante deberá registrarse.

Ejemplos:

Cambio de configuración

Cambio de agente

Transferencia

Cambio de canal

Actualización de Prompt

Cambio de Policies

Nunca eliminar registros.

---

# SOFT DELETE

No eliminar registros importantes.

Utilizar:

deleted_at

cuando corresponda.

Las conversaciones deberán mantenerse para auditoría.

---

# FOREIGN KEYS

Toda relación deberá utilizar claves foráneas.

No utilizar relaciones implícitas.

---

# ÍNDICES

Crear índices para:

organization_id

Opportunity_id

agent_id

channel_id

external_user_id

provider_message_id

created_at

Nunca esperar a que el sistema crezca para indexar.

---

# UUID

Todas las entidades públicas deberán utilizar UUID.

No exponer IDs autoincrementales.

Los IDs internos podrán seguir siendo enteros si mejora el rendimiento, pero las APIs deberán trabajar con UUID.

---

# METADATA

Las tablas podrán incluir un campo metadata JSON cuando sea necesario.

Nunca crear columnas específicas para información exclusiva de un Provider.

Ejemplo:

Telegram update_id

WhatsApp webhook_id

Slack thread_ts

Todos estos datos deberán almacenarse como metadata.

---

# FECHAS

Todas las fechas deberán almacenarse en UTC.

Nunca almacenar fechas locales.

La conversión de zona horaria deberá realizarse únicamente en el Dashboard.

---

# REGLAS DE PERSISTENCIA

Toda escritura seguirá este flujo.

Runtime

↓

Service

↓

Repository

↓

Unit of Work

↓

SQLAlchemy

↓

Base de datos

Nunca saltarse capas.

---

# PRINCIPIO FUNDAMENTAL

El dominio nunca deberá saber cómo se almacenan los datos.

La persistencia es un detalle de implementación.

Debe poder reemplazarse sin modificar el comportamiento del sistema.

# WORKFLOW ENGINE

El Workflow Engine representa el sistema de automatización de la plataforma.

Su responsabilidad será coordinar procesos completos del negocio.

El Workflow Engine no reemplaza al Runtime.

El Runtime utiliza el Workflow Engine cuando una conversación requiere ejecutar un proceso.

---

# FILOSOFÍA

Un mensaje no siempre requiere llamar al LLM.

Algunos mensajes representan procesos.

Ejemplos:

Agendar una cita.

Consultar un pedido.

Solicitar una factura.

Cancelar una reserva.

Actualizar información.

Consultar disponibilidad.

Todos estos procesos deberán implementarse mediante Workflows.

No mediante Prompts.

---

# RESPONSABILIDADES

El Workflow Engine deberá ser responsable de:

• identificar workflows

• validar condiciones

• ejecutar pasos

• controlar errores

• coordinar herramientas

• devolver resultados

Nunca deberá construir prompts.

Nunca deberá responder conversaciones.

---

# PRINCIPIO FUNDAMENTAL

El Runtime decide.

El Workflow ejecuta.

El LLM razona.

Cada componente tiene una única responsabilidad.

---

# ESTRUCTURA

Todo Workflow estará compuesto por una secuencia de Steps.

Workflow

↓

Step

↓

Step

↓

Step

↓

Resultado

Cada Step será completamente independiente.

---

# STEP

Un Step representa una única acción.

Ejemplos:

Consultar inventario.

Consultar agenda.

Crear pedido.

Enviar correo.

Generar PDF.

Guardar información.

Nunca mezclar múltiples responsabilidades en un mismo Step.

---

# TIPOS DE STEP

El sistema deberá soportar diferentes tipos.

Tool Step

Ejecuta una herramienta.

LLM Step

Solicita razonamiento.

Condition Step

Evalúa condiciones.

Delay Step

Espera un tiempo determinado.

Human Step

Requiere intervención humana.

Webhook Step

Invoca un servicio HTTP.

SubWorkflow Step

Ejecuta otro Workflow.

---

# WORKFLOW CONTEXT

Todo Workflow deberá compartir un contexto.

El contexto contendrá únicamente datos necesarios para la ejecución.

Nunca deberá contener objetos de infraestructura.

---

# WORKFLOW STATE

Cada Workflow tendrá un estado.

PENDING

RUNNING

WAITING

FAILED

COMPLETED

CANCELLED

---

# WORKFLOW HISTORY

Toda ejecución deberá quedar registrada.

Como mínimo:

inicio

fin

duración

steps ejecutados

resultado

errores

usuario

agente

conversación

---

# WORKFLOW REGISTRY

Todos los Workflows deberán registrarse automáticamente.

Nunca instanciarlos manualmente.

El Runtime únicamente solicitará:

Obtener Workflow

Ejecutar Workflow

Nada más.

---

# TOOL ENGINE

El Tool Engine administra todas las herramientas.

Nunca el LLM.

Nunca el Runtime.

---

# RESPONSABILIDADES

Registrar herramientas.

Descubrir herramientas.

Validar permisos.

Ejecutar herramientas.

Registrar auditoría.

Controlar tiempos.

Controlar errores.

---

# TOOL

Toda herramienta deberá implementar exactamente la misma interfaz.

Como mínimo:

name

description

input_schema

output_schema

validate()

execute()

health()

---

# VALIDACIÓN

Toda herramienta deberá validar sus parámetros antes de ejecutarse.

Nunca confiar en el LLM.

Nunca asumir que los parámetros son correctos.

---

# PERMISOS

Cada herramienta deberá declarar permisos.

Ejemplos:

Lectura.

Escritura.

Administración.

Acceso externo.

Datos sensibles.

El Runtime validará estos permisos antes de ejecutar.

---

# AISLAMIENTO

Una herramienta nunca deberá conocer otra herramienta.

Toda coordinación será responsabilidad del Workflow.

---

# TIMEOUT

Toda herramienta deberá definir un timeout.

Si excede el tiempo máximo:

cancelar ejecución

registrar error

continuar según política

Nunca bloquear el Runtime.

---

# RETRIES

Las herramientas podrán definir políticas de reintento.

Ejemplos:

3 intentos

Backoff exponencial

Retry inmediato

Retry manual

Todo configurable.

---

# CIRCUIT BREAKER

Toda herramienta externa deberá soportar Circuit Breaker.

Si un servicio falla repetidamente:

dejar de invocarlo

registrar el estado

reintentar posteriormente

---

# CACHE

Las herramientas podrán utilizar cache.

Ejemplos:

Consultar tasa de cambio.

Consultar clima.

Consultar inventario.

Nunca recalcular información innecesariamente.

---

# AUDITORÍA

Toda ejecución deberá registrar:

herramienta

usuario

agente

duración

resultado

error

fecha

Nunca ejecutar herramientas sin auditoría.

---

# OBSERVABILIDAD

Registrar:

inicio

fin

errores

timeout

retries

latencia

resultado

---

# LLM

El proveedor IA nunca ejecutará herramientas.

Nunca consultará bases de datos.

Nunca llamará APIs.

Nunca tomará decisiones de infraestructura.

El proveedor IA únicamente recibe contexto.

Y devuelve texto.

Nada más.

---

# DECISIONES

Quien decide ejecutar una herramienta es el Runtime.

No el LLM.

Ejemplo conceptual.

Usuario

↓

Runtime

↓

¿Existe un Workflow?

↓

Sí

↓

Ejecutar Workflow

↓

No

↓

¿Existe una Tool apropiada?

↓

Sí

↓

Ejecutar Tool

↓

No

↓

Consultar LLM

↓

Responder

El LLM será siempre el último recurso.

Nunca el primero.

---

# PRINCIPIO FUNDAMENTAL

La inteligencia del sistema reside en el Runtime.

No en el proveedor IA.

Mientras menos decisiones dependa del LLM, más determinista, auditable y mantenible será la plataforma.

# DECISION ENGINE

El Decision Engine representa el cerebro operativo de la plataforma.

Toda decisión del negocio deberá pasar por este componente.

El Runtime nunca deberá contener reglas del negocio.

El Runtime únicamente coordina.

El Decision Engine decide.

---

# FILOSOFÍA

El LLM nunca deberá tomar decisiones del negocio.

El Runtime nunca deberá contener reglas específicas.

Toda decisión deberá centralizarse en un único lugar.

Esto permite:

- auditoría
- mantenibilidad
- trazabilidad
- pruebas unitarias
- configuración dinámica

---

# RESPONSABILIDADES

El Decision Engine será responsable de:

• validar solicitudes

• aplicar políticas

• seleccionar agentes

• seleccionar herramientas

• seleccionar workflows

• validar permisos

• determinar restricciones

• decidir si utilizar IA

• decidir si responder

• decidir si transferir a un humano

• decidir si finalizar una conversación

---

# PRINCIPIO FUNDAMENTAL

Toda decisión deberá poder explicarse.

Nunca deberán existir decisiones "mágicas".

Cada decisión deberá poder responder:

¿Por qué ocurrió?

---

# ENTRADA

El Decision Engine recibirá:

Opportunity

Agent

Organization

User

Incoming Message

Current State

Capabilities

Policies

Configuration

Context

---

# SALIDA

Nunca devolverá texto.

Nunca responderá al usuario.

Siempre devolverá una decisión estructurada.

Ejemplo conceptual:

Decision

tipo

acciones

workflow

tool

next_agent

reason

metadata

---

# TIPOS DE DECISIÓN

El sistema deberá soportar al menos:

CONTINUE

RESPOND

RUN_WORKFLOW

RUN_TOOL

TRANSFER_AGENT

TRANSFER_HUMAN

BLOCK

IGNORE

END_Opportunity

ASK_FOR_MORE_INFORMATION

---

# REGLAS

Las reglas deberán ser pequeñas.

Cada regla tendrá una única responsabilidad.

Nunca escribir reglas gigantes.

---

# EJEMPLOS

Regla:

Horario laboral.

Entrada:

Hora actual.

Salida:

Permitir responder.

o

Transferir.

---

Regla:

Cliente VIP.

Entrada:

Usuario.

Salida:

Asignar agente Premium.

---

Regla:

Idioma.

Entrada:

Mensaje.

Salida:

Cambiar idioma del agente.

---

Regla:

Presupuesto diario.

Entrada:

Consumo IA.

Salida:

Utilizar modelo económico.

---

# PIPELINE

Todas las reglas deberán ejecutarse mediante un Pipeline.

Entrada

↓

Rule 1

↓

Rule 2

↓

Rule 3

↓

Rule 4

↓

Resultado

Cada regla recibe el resultado anterior.

---

# PRIORIDADES

Las reglas podrán definir prioridad.

Ejemplo:

Seguridad

↓

Cumplimiento legal

↓

Permisos

↓

Negocio

↓

Optimización

↓

Experiencia del usuario

Nunca ejecutar reglas críticas al final.

---

# CONFLICTOS

Cuando dos reglas produzcan decisiones incompatibles:

Siempre ganará la regla de mayor prioridad.

Nunca depender del orden del código.

---

# ORGANIZATION POLICIES

Cada Organización podrá definir reglas propias.

Ejemplos:

Horario.

Idiomas.

Modelos permitidos.

Canales permitidos.

Herramientas permitidas.

---

# AGENT POLICIES

Cada Agente podrá agregar reglas adicionales.

Nunca reemplazar las reglas de la Organización.

Siempre complementarlas.

---

# CHANNEL POLICIES

Cada canal podrá declarar restricciones.

Ejemplos:

Tamaño máximo.

Tipos de archivo.

Rate Limits.

Formato.

Tiempo de respuesta.

Nunca codificar estas restricciones dentro del Runtime.

---

# SECURITY POLICIES

Ejemplos:

No revelar prompts.

No revelar herramientas.

No revelar configuración.

No ejecutar herramientas restringidas.

No responder datos privados.

No permitir Prompt Injection.

Toda política de seguridad deberá ejecutarse antes del LLM.

---

# COST POLICIES

El sistema deberá poder decidir:

Utilizar GPT-4.

Utilizar GPT-4 Mini.

Utilizar Claude.

Utilizar Ollama.

según:

presupuesto

usuario

agente

organización

horario

prioridad

Nunca dejar esta decisión fija.

---

# ESCALATION POLICIES

El sistema deberá decidir cuándo transferir.

Ejemplos:

Confianza baja.

Usuario molesto.

Solicitud explícita.

Tema sensible.

Herramienta falló.

Workflow falló.

---

# TOOL POLICIES

Antes de ejecutar una herramienta deberá validarse:

Permisos.

Estado.

Timeout.

Límites.

Dependencias.

Disponibilidad.

---

# AI POLICIES

Antes de consultar un LLM deberá validarse:

Modelo disponible.

Presupuesto.

Rate Limit.

Proveedor saludable.

Tokens máximos.

---

# AUDITORÍA

Toda decisión deberá registrarse.

Como mínimo:

fecha

regla aplicada

entrada

salida

resultado

duración

---

# OBSERVABILIDAD

Cada decisión deberá poder reconstruirse.

Nunca deberán existir decisiones invisibles.

---

# TESTABILIDAD

Cada regla deberá poder probarse independientemente.

No crear reglas dependientes unas de otras.

Cada regla deberá tener pruebas unitarias.

---

# PRINCIPIO FUNDAMENTAL

Las reglas del negocio nunca deberán vivir:

• en el Prompt

• en el Runtime

• en los Providers

• en los Workflows

Las reglas pertenecen exclusivamente al Decision Engine.

# EXECUTION PIPELINE

El Execution Pipeline representa el flujo oficial de procesamiento de todos los mensajes.

Todo mensaje deberá recorrer exactamente el mismo Pipeline.

No deberán existir caminos alternativos.

No deberán existir llamadas directas entre motores.

Cada motor únicamente recibe un Context y devuelve un Context actualizado.

---

# FILOSOFÍA

El sistema estará compuesto por motores independientes.

Cada motor tendrá exactamente una responsabilidad.

Los motores nunca conocerán la implementación interna de otros motores.

Todos trabajarán sobre un único objeto compartido denominado:

Execution Context.

---

# PRINCIPIO FUNDAMENTAL

Cada motor debe ser:

Independiente.

Reutilizable.

Testeable.

Observable.

Determinista cuando sea posible.

---

# EXECUTION CONTEXT

Todo el Pipeline compartirá un único contexto.

El contexto contendrá toda la información necesaria para procesar un mensaje.

Ejemplo conceptual:

ExecutionContext

organization

Opportunity

agent

user

channel

incoming_message

memory

knowledge

workflow

decision

reasoning

response

metadata

metrics

errors

Nunca utilizar variables globales.

Nunca compartir estado mediante Singletons.

Todo deberá viajar dentro del Execution Context.

---

# PIPELINE OFICIAL

Todo mensaje seguirá exactamente el siguiente flujo.

Incoming Message

↓

Normalization Engine

↓

Security Engine

↓

Decision Engine

↓

Opportunity Engine

↓

Memory Engine

↓

Knowledge Engine

↓

Workflow Engine

↓

Reasoning Engine

↓

Response Engine

↓

Persistence Engine

↓

Channel Provider

↓

Metrics Engine

↓

Audit Engine

---

# NORMALIZATION ENGINE

Responsabilidad.

Convertir cualquier mensaje recibido a un formato interno único.

Ejemplos.

Telegram.

WhatsApp.

Messenger.

Instagram.

Todos deberán producir exactamente el mismo modelo interno.

---

# SECURITY ENGINE

Responsabilidad.

Validar la seguridad del mensaje.

Ejemplos.

Firma del webhook.

Rate limit.

Prompt Injection.

Spam.

Contenido malicioso.

Archivos peligrosos.

Nunca permitir que un mensaje inseguro llegue al Runtime.

---

# DECISION ENGINE

Responsabilidad.

Aplicar reglas del negocio.

No consultar IA.

No consultar herramientas.

No generar respuestas.

Únicamente decidir.

---

# Opportunity ENGINE

Responsabilidad.

Administrar el estado de la conversación.

Crear.

Actualizar.

Cerrar.

Transferir.

Nunca llamar al proveedor IA.

---

# MEMORY ENGINE

Responsabilidad.

Construir la memoria conversacional.

Nunca consultar el proveedor IA.

---

# KNOWLEDGE ENGINE

Responsabilidad.

Consultar conocimiento externo.

Ejemplos.

PDF.

FAQ.

Base documental.

RAG.

Wiki.

Nunca generar respuestas.

---

# WORKFLOW ENGINE

Responsabilidad.

Ejecutar procesos de negocio.

Nunca construir prompts.

Nunca responder usuarios.

---

# REASONING ENGINE

Responsabilidad.

Resolver problemas utilizando IA cuando sea necesario.

El Reasoning Engine podrá decidir:

utilizar GPT

utilizar Claude

utilizar Gemini

utilizar Ollama

utilizar múltiples modelos

utilizar caché

reutilizar respuestas

comparar resultados

aplicar fallback

Toda decisión relacionada con IA pertenece exclusivamente aquí.

---

# RESPONSE ENGINE

Responsabilidad.

Construir la respuesta final.

Podrá:

agregar formato

adjuntar archivos

agregar botones

agregar imágenes

fragmentar mensajes largos

adaptar la respuesta al canal

Nunca consultar IA.

Nunca ejecutar herramientas.

---

# PERSISTENCE ENGINE

Responsabilidad.

Persistir toda la información generada durante la ejecución.

Nunca ejecutar reglas.

Nunca consultar IA.

Nunca enviar mensajes.

---

# METRICS ENGINE

Responsabilidad.

Registrar métricas.

Tiempo.

Costo.

Tokens.

Modelo.

Herramientas.

Workflow.

Usuario.

Organización.

---

# AUDIT ENGINE

Responsabilidad.

Registrar absolutamente todas las decisiones importantes.

Toda ejecución deberá poder reconstruirse posteriormente.

---

# ENGINE CONTRACT

Todos los motores deberán implementar exactamente la misma interfaz.

Ejemplo conceptual.

Engine

↓

execute(context)

↓

ExecutionContext

Nunca crear interfaces distintas para cada motor.

---

# ENGINE REGISTRY

Todos los motores deberán registrarse automáticamente.

El Pipeline únicamente conocerá el Registry.

Nunca instanciar motores manualmente.

---

# PIPELINE CONFIGURATION

El Pipeline deberá ser configurable.

Ejemplo.

Security Engine

↓

Decision Engine

↓

Memory Engine

↓

Reasoning Engine

↓

Response Engine

Mañana podrá agregarse.

Moderation Engine.

Translation Engine.

Billing Engine.

Analytics Engine.

Sin modificar el resto del sistema.

---

# OBSERVABILIDAD

Cada motor deberá registrar.

inicio.

fin.

duración.

errores.

resultado.

Nunca deberán existir pasos invisibles.

---

# PRINCIPIO FUNDAMENTAL

Toda inteligencia de la plataforma deberá surgir de la composición de motores pequeños, independientes y especializados.

Nunca construir motores gigantes que acumulen responsabilidades.

Mientras más simple sea cada motor, más poderosa será la plataforma completa.

# TASK ENGINE

El Task Engine representa el sistema oficial de ejecución de trabajo de la plataforma.

Todo proceso del negocio deberá ejecutarse mediante Tasks.

Nunca ejecutar lógica compleja directamente desde el Runtime.

Nunca ejecutar procesos completos dentro de un Workflow.

Los Workflows únicamente describen procesos.

Las Tasks realizan el trabajo.

---

# FILOSOFÍA

Toda automatización se compone de pequeñas tareas independientes.

Cada Task deberá tener una única responsabilidad.

Nunca crear Tasks gigantes.

Mientras más pequeñas sean las Tasks, mayor será la capacidad de reutilización.

---

# PRINCIPIO FUNDAMENTAL

Las conversaciones generan trabajo.

El trabajo se representa mediante Tasks.

Las Tasks producen resultados.

Los resultados generan respuestas.

---

# TASK

Una Task representa una unidad mínima de trabajo.

Una Task deberá ser:

Atómica.

Reutilizable.

Idempotente.

Observable.

Testeable.

Cancelable.

Reintentable.

---

# RESPONSABILIDADES

Una Task podrá:

Consultar una API.

Consultar una base de datos.

Consultar memoria.

Ejecutar una herramienta.

Generar un archivo.

Enviar un correo.

Actualizar un CRM.

Construir un Prompt.

Solicitar razonamiento.

Persistir información.

Nunca realizar múltiples responsabilidades.

---

# TASK CONTRACT

Toda Task deberá implementar exactamente la misma interfaz.

Conceptualmente.

Task

↓

execute(context)

↓

TaskResult

Toda Task devolverá un resultado estructurado.

Nunca texto libre.

---

# TASK RESULT

Toda Task devolverá.

Estado.

Datos.

Errores.

Duración.

Metadata.

Nunca lanzar errores no controlados.

---

# TASK STATE

Todas las Tasks tendrán uno de los siguientes estados.

PENDING

READY

RUNNING

WAITING

RETRYING

FAILED

CANCELLED

COMPLETED

SKIPPED

---

# TASK CONTEXT

Toda Task recibirá exactamente el mismo contexto.

Execution Context.

Nunca parámetros arbitrarios.

Nunca variables globales.

---

# TASK REGISTRY

Todas las Tasks deberán registrarse automáticamente.

Nunca instanciar Tasks manualmente.

El Runtime únicamente solicitará.

Obtener Task.

Ejecutar Task.

---

# TASK GRAPH

Los procesos deberán representarse mediante un grafo dirigido.

No únicamente una secuencia lineal.

Ejemplo.

Task A

↓

Task B

↓

Task C

↓

Task D

pero también.

Task A

↓

Task B

↓

Task C

↓

Task D

↓

Task E

↓

Task F

↓

Task G

permitiendo ramas paralelas.

---

# DEPENDENCIAS

Toda Task podrá declarar dependencias.

Ejemplo.

Reservar cita.

requiere.

Consultar disponibilidad.

Nunca ejecutar Tasks antes de cumplir sus dependencias.

---

# REINTENTOS

Cada Task podrá definir.

Cantidad máxima.

Backoff.

Timeout.

Retry automático.

Retry manual.

---

# TIMEOUT

Toda Task deberá declarar un tiempo máximo.

Nunca permitir Tasks bloqueadas indefinidamente.

---

# IDEMPOTENCIA

Toda Task deberá poder ejecutarse múltiples veces sin producir resultados inconsistentes.

Este requisito es obligatorio.

---

# TASK TYPES

El sistema deberá soportar.

Reasoning Task.

Tool Task.

Persistence Task.

Notification Task.

Knowledge Task.

Memory Task.

Validation Task.

Transformation Task.

Routing Task.

Integration Task.

---

# TASK EXECUTION

El Runtime nunca ejecutará lógica directamente.

Siempre delegará trabajo a una Task.

---

# TASK QUEUE

La arquitectura deberá permitir incorporar una cola de ejecución.

Inicialmente todas las Tasks podrán ejecutarse sincrónicamente.

Posteriormente deberán poder ejecutarse mediante.

Celery.

RabbitMQ.

Redis Streams.

Kafka.

Sin modificar el Runtime.

---

# TASK OBSERVABILITY

Toda Task deberá registrar.

Inicio.

Fin.

Tiempo.

Resultado.

Errores.

Reintentos.

Dependencias.

---

# TASK AUDIT

Toda ejecución deberá quedar almacenada.

Esto permitirá reconstruir cualquier proceso.

---

# TASK VERSIONING

Las Tasks deberán poder evolucionar sin romper ejecuciones anteriores.

Nunca modificar una Task activa sin versionarla.

---

# TASK LIBRARY

Las Tasks deberán ser reutilizables.

Ejemplos.

Consultar Inventario.

Reservar Agenda.

Enviar Email.

Consultar CRM.

Construir Prompt.

Generar PDF.

Nunca duplicar lógica.

---

# PRINCIPIO FUNDAMENTAL

Toda automatización deberá componerse mediante pequeñas Tasks reutilizables.

Nunca mediante funciones gigantes.

Mientras más pequeñas sean las Tasks, más poderosa será la plataforma.
