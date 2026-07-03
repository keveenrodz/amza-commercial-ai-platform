# 02 – Product Glossary

## Objetivo

Este documento define el lenguaje oficial del proyecto.

Todos los documentos, el código fuente, la base de datos, la API, el Dashboard y la documentación deberán utilizar exactamente estos términos.

No deberán inventarse sinónimos.

No deberán existir múltiples nombres para un mismo concepto.

Cuando exista una duda sobre el significado de una palabra, este documento tendrá prioridad sobre cualquier otro.

---

# Organización (Organization)

Empresa que utiliza la plataforma para administrar su operación comercial.

Una Organización puede tener:

* AI Assistants
* Advisors or Human
* Channels
* Products
* Business Knowledge
* Conversations
* Opportunities
* Assets
* Configuraciones

En el MVP existirá una única Organización (Amza Empaques), pero la arquitectura deberá permitir múltiples organizaciones en el futuro.

---

# Internal User

Persona que utiliza el Dashboard.

Representa a un empleado de la empresa.

Ejemplos:

* asesora comercial
* administrador
* gerente

Nunca representa al cliente final.

---

# Contact

Persona que inicia una conversación.

Todavía no existe evidencia suficiente para considerarlo cliente.

Todo Contact puede convertirse posteriormente en una Opportunity o en un Customer.

---

# Opportunity

Contacto con potencial comercial.

Una Opportunity representa una posible venta.

La plataforma deberá ayudar a que ninguna Opportunity se pierda por falta de atención o seguimiento.

Este es uno de los conceptos más importantes del proyecto.

---

# Customer

Contacto que ya realizó al menos una compra.

Todos los Customers son Contacts.

No todos los Contacts son Customers.

---

# Conversation

Interacción completa entre un Contact y la empresa.

Una Conversation es independiente del canal utilizado.

Puede comenzar en Telegram y, en versiones futuras, continuar en WhatsApp u otros canales si la estrategia del negocio lo requiere.

Toda Conversation mantiene su historial completo.

---

# Message

Unidad mínima de comunicación dentro de una Conversation.

Un Message puede ser:

* texto
* imagen
* video
* documento
* audio
* ubicación
* otro tipo soportado por el Channel correspondiente

---

# Channel

Medio por el cual ocurre una Conversation.

Ejemplos:

* Telegram
* WhatsApp
* Instagram
* Facebook Messenger

El Core nunca dependerá de un Channel específico.

---

# Unified Inbox

Vista unificada donde el equipo comercial visualiza todas las Conversations independientemente del Channel de origen.

Representa el centro operativo del proceso comercial.

---

# AI Assistant

Componente inteligente responsable de atender automáticamente aquellas conversaciones que no requieren criterio humano.

El AI Assistant nunca reemplaza completamente a un Advisor.

Su función es asistir el proceso comercial.

---

# Advisor

Persona responsable de atender conversaciones que requieren criterio humano.

Ejemplos:

* cotizaciones complejas
* negociaciones
* consultas especiales
* reclamaciones
* solicitudes fuera del alcance del AI Assistant

---

# Attention Ownership

Estado que indica quién posee actualmente el control de una Conversation.

El propietario podrá ser:

* AI Assistant
* Advisor or Human

El control podrá cambiar múltiples veces durante una misma Conversation.

El cliente nunca debería percibir estos cambios.

---

# Business Knowledge

Conjunto de información utilizada para responder correctamente a los clientes.

Puede provenir de múltiples fuentes.

Ejemplos:

* catálogo de productos
* listas de precios
* reglas comerciales
* archivos Excel
* fórmulas de cotización
* imágenes
* videos
* documentos PDF
* inventario
* sistemas externos como SIIGO
* futuras bases documentales

La plataforma nunca deberá asumir que el conocimiento proviene de una única fuente.

---

# Product

Artículo comercializado por la empresa.

Un Product puede tener diferentes variantes y configuraciones.

---

# Product Variant

Versión específica de un Product.

Puede diferenciarse por:

* tamaño
* capacidad
* material
* color
* acabado
* otras características comerciales

---

# Product Customization

Modificación realizada sobre un Product.

Existen dos tipos principales.

## Standard Customization

Personalización de un producto existente sin modificar su diseño estructural.

Ejemplo.

Impresión de un logo sobre una bolsa existente.

Estas personalizaciones podrán ser atendidas por el AI Assistant cuando las reglas comerciales estén completamente definidas.

---

## Custom Development

Creación de un nuevo producto o modificación de dimensiones, materiales o diseño estructural.

Estos casos requerirán inicialmente intervención humana.

En futuras versiones podrán automatizarse parcialmente.

---

# Quotation

Propuesta comercial enviada a un Contact.

Puede ser:

* estándar
* personalizada

La plataforma deberá registrar todas las Quotations para facilitar el seguimiento posterior.

---

# Follow-up

Actividad realizada después de una Quotation o de una Conversation importante con el objetivo de aumentar la probabilidad de cerrar una venta.

El sistema deberá ayudar al equipo comercial a identificar qué Follow-ups deben realizarse.

---

# Asset

Recurso digital utilizado durante una Conversation.

Ejemplos:

* fotografías
* videos
* fichas técnicas
* catálogos
* documentos PDF
* archivos descargables

Los Assets forman parte del Business Knowledge.

---

# Business Rule

Regla definida por el negocio.

Ejemplos:

* cálculo de cotizaciones
* cantidades mínimas
* tiempos de producción
* descuentos
* restricciones

Las Business Rules deberán mantenerse separadas del código cuando sea posible.

---

# Runtime

Motor responsable de coordinar la atención de una Conversation.

No contiene reglas específicas del negocio.

Únicamente orquesta los componentes del sistema.

---

# Provider

Adaptador responsable de comunicarse con un sistema externo.

Ejemplos:

* Telegram Provider
* WhatsApp Provider
* OpenRouter Provider
* SIIGO Provider

El Runtime nunca dependerá directamente de un Provider.

---

# Dashboard

Aplicación utilizada por los Internal Users para administrar la operación comercial.

Desde aquí podrán:

* visualizar Conversations;
* responder manualmente;
* consultar Follow-ups;
* administrar AI Assistants;
* revisar Opportunities;
* configurar la plataforma.

---

# Principio fundamental

Todo el proyecto deberá utilizar exactamente este lenguaje.

Cuando sea necesario incorporar un nuevo concepto, primero deberá añadirse a este documento y posteriormente utilizarse en el resto de la plataforma.

Mantener un lenguaje consistente es un requisito de calidad del producto y de la arquitectura.

