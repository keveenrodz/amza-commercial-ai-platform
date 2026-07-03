# ROADMAP

Este documento define la evolución de la plataforma.

No describe la arquitectura.

No describe la implementación.

Describe únicamente la estrategia de evolución del producto.

El objetivo es construir una plataforma estable, mantenible y utilizable desde la primera versión, evitando desarrollar funcionalidades que todavía no generan valor.

Cada fase deberá ser completamente funcional antes de iniciar la siguiente.
Se debe de testear y probar que cada funcionalidad funcione correctamente.

Nunca comenzar una nueva fase con errores pendientes en la anterior.

La prioridad será siempre:

Calidad > Cantidad.

---

# VISIÓN

La visión del proyecto consiste en construir una plataforma de operaciones comerciales asistidas por Inteligencia Artificial que permita a las pequeñas y medianas empresas atender mejor a sus clientes, aumentar sus ventas y eliminar los cuellos de botella del proceso comercial mediante una atención híbrida entre IA y personas.

La plataforma deberá permitir integrar distintos canales de comunicación, distintos modelos de IA y distintas herramientas empresariales sin modificar el núcleo del sistema.

El objetivo NO es competir con plataformas como:

- LangGraph
- n8n
- CrewAI
- Temporal
- OpenAI Agents

Por el contrario.

Cuando dichas herramientas aporten valor deberán poder integrarse como parte de la plataforma.

El objetivo es construir una plataforma que permita utilizarlas de forma sencilla para resolver problemas empresariales.

---

# PRINCIPIOS

Toda nueva funcionalidad deberá cumplir los siguientes criterios.

Debe resolver un problema real.

Debe ser reutilizable.

Debe respetar la arquitectura.

Debe ser fácilmente mantenible.

Debe poder probarse automáticamente.

Debe generar valor para el usuario.

Si una funcionalidad no cumple estos criterios, deberá posponerse.

---

# MVP

Objetivo.

Validar que una atención comercial híbrida (IA + Humano) mejora el proceso comercial de Amza Empaques.

Tiempo estimado.

4 a 6 semanas.

El MVP deberá permitir:

✓ Telegram

✓ Un único Agente

✓ OpenRouter

✓ Dashboard

✓ Conversaciones

✓ Historial

✓ Cambio IA/Humano

✓ Configuración básica

✓ Memoria reciente

✓ SQLite

✓ FastAPI

✓ NextJS Dashboard

✓ Docker

✓ Logs

✓ Deploy

No deberá incluir:

RAG

Embeddings

Knowledge Base

WhatsApp

Workflows

Task Engine

Múltiples agentes

Autenticación

Roles

Analytics

Facturación

Streaming

Audio

Imágenes

Multiempresa

Marketplace

El objetivo del MVP es demostrar que la plataforma reduce el trabajo repetitivo, mejora los tiempos de respuesta, facilita el seguimiento comercial y ayuda a aumentar la conversión de ventas.

Nada más.

---

# VERSIÓN 1.1: Validación Comercial

Objetivo.

Convertir el MVP en un producto estable.

Tiempo estimado.

2 semanas.

Agregar.

Mejor manejo de errores.

Health Checks.

Configuración desde Dashboard.

Versionado de configuración.

Backups.

Mejor logging.

Pruebas automáticas.

Observabilidad.

Optimización de rendimiento.

No agregar nuevas funcionalidades de negocio.

---

# VERSIÓN 1.5: Validación Comercial

Objetivo.

Incorporar el segundo canal.

Agregar.

WhatsApp Cloud API.

Adaptador reutilizando exactamente el mismo Runtime.

Validación completa de Webhooks.

Configuración desde Dashboard.

Sin modificar el Core.

El éxito de esta fase consiste en comprobar que realmente la arquitectura es multicanal.

---

# VERSIÓN 2: Operación Comercial

Objetivo.

Convertir el agente en un asistente empresarial.

Agregar.

Múltiples Agentes.

Prompt Builder.

Agent Definition System.

Configuración completa.

Knowledge Base básica.

Carga de documentos.

Búsqueda documental.

Herramientas simples.

Transferencia entre agentes.

CRM.

Seguimientos.

Recordatorios.

Pipeline comercial.

Clientes prioritarios.

PostgreSQL.

Autenticación.

Usuarios.

Roles.

Permisos.

El sistema deberá seguir siendo sencillo de utilizar.

---

# VERSIÓN 3: Automatización Comercial

Objetivo.

Automatizar procesos.

Agregar.

Workflow Engine.

Task Engine.

Herramientas reutilizables.

Integraciones.

Correo.

Calendario.

Seguimientos automáticos.
CRM integrado.
Cotizaciones.
SIIGO.
Email.
Agenda.
Workflows.

ERP.

APIs externas.

Versionado de agentes.

Versionado de prompts.

Políticas configurables.

RAG.

Embeddings.

Memoria semántica.

Esta versión transforma el sistema en una plataforma de automatización.

---

# VERSIÓN 4: Escalabilidad

Objetivo.

Escalar la plataforma.

Agregar.

Multiempresa.

Múltiples organizaciones.

Facturación.

Organizaciones.

Roles.

Límites.

Cuotas.

Métricas.

Analytics.

Dashboards.

Colas.

Redis.

Celery.

Cache.

Escalabilidad horizontal.

Alta disponibilidad.

El objetivo será soportar múltiples clientes simultáneamente.

---

# VERSIÓN 5: Ecosistema

Objetivo.

Convertir la plataforma en un ecosistema.

Agregar.

Marketplace.

Plugins.

SDK.

API Pública.

Webhooks.

MCP.

Integración con LangGraph.

Integración con n8n.

Integración con Make.

Integración con Zapier.

Integración con Temporal.

Integración con OpenAI Agents.

Integración con CrewAI.

El objetivo ya no será únicamente responder conversaciones.

Será convertirse en una plataforma abierta.

---

# REGLA DE ORO

Nunca desarrollar una funcionalidad simplemente porque es interesante.

Toda funcionalidad deberá responder a una necesidad real.

---

# DEFINICIÓN DE TERMINADO

Una fase únicamente podrá considerarse terminada cuando:

Toda la documentación esté actualizada.

No existan errores críticos.

Las pruebas automáticas pasen.

El despliegue funcione.

La arquitectura permanezca limpia.

El usuario pueda utilizar la nueva funcionalidad sin asistencia técnica.

---

# FILOSOFÍA

La plataforma deberá evolucionar lentamente.

Cada nueva versión deberá simplificar la experiencia del usuario.

Nunca aumentar la complejidad innecesariamente.

Siempre preferir una plataforma pequeña, estable y elegante antes que una plataforma enorme difícil de mantener.

---

# VISIÓN FINAL

El objetivo nunca será construir la plataforma con más funcionalidades.

El objetivo será construir la plataforma más fácil de extender, más fácil de mantener y más útil para resolver problemas reales de empresas.

La calidad de la arquitectura siempre tendrá prioridad sobre la velocidad de desarrollo.
