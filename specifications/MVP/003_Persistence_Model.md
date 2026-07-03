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

