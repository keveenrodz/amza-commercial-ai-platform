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

