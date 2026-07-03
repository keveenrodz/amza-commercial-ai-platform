Plataforma para automatizar y asistir el proceso comercial de empresas mediante agentes de IA.

Una plataforma para crear asistentes empresariales inteligentes, donde puedas integrar fácilmente capacidades existentes (OpenRouter, Telegram, WhatsApp, n8n, LangGraph, MCP, RAG, etc.) sin reinventarlas, y donde el verdadero valor esté en la experiencia de configuración, la orquestación y la adaptación al negocio.

indicador de éxito

No mediría:

"Número de respuestas IA."

Mediría algo como esto.

Indicador	Objetivo
Tiempo primera respuesta	<30 segundos
Conversaciones respondidas	>98%
Seguimientos realizados	>95%
Cotizaciones perdidas	<5%
Tiempo dedicado a preguntas repetitivas	-80%
Conversión a venta	Incremento medible
Satisfacción del cliente	Incremento medible

Esos son KPIs de negocio.

No KPIs de IA.



Especificación de la Arquitectura (el "qué")

Todo lo que hemos escrito hasta ahora: principios, componentes, contratos y responsabilidades. Esto cambia poco y sirve de guía para toda la vida del proyecto.

Plan de Implementación Incremental (el "cómo")

Aquí definiríamos fases concretas, por ejemplo:

Fase 1 (MVP): Telegram, un agente, SQLite, un proveedor de IA, memoria reciente, dashboard básico.
Fase 2: WhatsApp, PostgreSQL, múltiples agentes, herramientas básicas.
Fase 3: Knowledge Base, RAG, Task Engine avanzado, Workflows complejos.
Fase 4: Multiempresa, autenticación, colas, escalabilidad horizontal.
Fase 5: Versionado de agentes, observabilidad avanzada, analítica, marketplace de herramientas.


Documento 1
Architecture.md

Es el que estamos escribiendo.

No tiene código.

No tiene dependencias.

No tiene rutas.

No tiene endpoints.

Solo explica la arquitectura.

No cambia casi nunca.

Documento 2
Roadmap.md

Este documento responde:

¿Cómo llegamos desde el MVP hasta la visión?

Por ejemplo:

Fase 1

Telegram

SQLite

1 agente

OpenRouter

Dashboard

Nada más.

Fase 2

WhatsApp

Postgres

Múltiples agentes

Knowledge Base

Fase 3

RAG

Herramientas

Versionado

Fase 4

Multiempresa

Marketplace

Analytics

etc.

Documento 3

Este sí será el importante.

Build_MVP.md

Y aquí quiero hacer un cambio radical.



Documentos:
- Build_MVP.md : Construir en unas pocas semanas una primera versión funcional, limpia y profesional, alineada con la arquitectura, pero sin implementar funcionalidades que aún no aportan valor.


Cómo trabajaría a partir de ahora
Congelar Architecture.md. Lo dejamos como referencia y solo se actualiza cuando haya una decisión arquitectónica importante.
Crear Roadmap.md. Definimos las fases (MVP, V2, V3...) y qué entra en cada una.
Escribir Build_MVP.md. Este será el documento que usará Claude Code para generar el código. Debe ser mucho más corto, específico y sin ambigüedades.
Implementar por iteraciones. Cuando el MVP esté funcionando, usamos el Roadmap para incorporar capacidades una por una, validando que realmente aportan valor antes de aumentar la complejidad.


Creo que el flujo correcto debería ser este.

docs/

00_Vision.md                  ← Qué problema resolvemos

01_Engineering_Principles.md  ← Cómo escribimos software

02_Architecture.md            ← Cómo está diseñado

03_Roadmap.md                 ← Cómo evolucionará

04_Product_Specification.md   ← Qué es el MVP

specifications/

MVP/

001_Project_Setup.md

002_Backend_API.md

003_Database.md

004_Telegram.md

005_Runtime.md

006_Reasoning.md

007_Dashboard.md

008_Deployment.md

009_Testing.md

010_Acceptance.md
