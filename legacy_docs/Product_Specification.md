# 06 – Product Specification (MVP)

## Objetivo

El propósito del MVP es validar que una plataforma de atención comercial híbrida puede mejorar significativamente el proceso comercial de una empresa sin modificar su forma habitual de trabajar.

El MVP no busca automatizar todo el proceso comercial.

Su objetivo es eliminar el trabajo repetitivo, reducir los tiempos de respuesta y evitar la pérdida de oportunidades comerciales.

El primer caso de uso será Amza Empaques.

---

# Usuarios del producto

El MVP tendrá dos tipos de usuarios.

## Cliente

Persona que contacta a la empresa buscando información, productos o cotizaciones.

No conoce la plataforma.

Únicamente interactúa mediante canales conversacionales.

---

## Internal User

Empleado de la empresa encargado de administrar conversaciones, realizar cotizaciones complejas y hacer seguimiento comercial.

Toda la experiencia del Dashboard estará diseñada para este tipo de usuario.

---

# Problema actual

Actualmente la atención comercial depende completamente de dos asesoras.

El crecimiento del número de conversaciones ha convertido la atención en el principal cuello de botella del negocio.

Como consecuencia:

* algunas consultas tardan demasiado en responderse;
* se pierden oportunidades comerciales;
* el seguimiento a cotizaciones es insuficiente;
* gran parte del tiempo se dedica a responder preguntas repetitivas.

---

# Objetivo funcional

El sistema deberá convertirse en el centro operativo de la atención comercial.

Toda conversación deberá pasar por la plataforma.

La plataforma decidirá si la conversación puede ser atendida por el AI Assistant o requiere intervención de un Advisor.

---

# Capacidades del MVP

## Recepción de conversaciones

La plataforma deberá recibir conversaciones desde un canal conversacional.

La primera implementación utilizará Telegram únicamente como entorno de validación.

La arquitectura deberá permitir incorporar posteriormente WhatsApp sin modificar el Core.

---

## Atención automática

El AI Assistant deberá responder automáticamente consultas repetitivas relacionadas con:

* catálogo;
* productos;
* materiales;
* precios estándar;
* preguntas frecuentes;
* imágenes;
* sugerencias y recomendaciones de productos y soluciones.
* documentos comerciales.

---

## Escalamiento a humano

Cuando la conversación requiera criterio humano, la plataforma deberá asignarla automáticamente a un Advisor o Human.

Ejemplos:

* cotizaciones complejas;
* nuevos desarrollos o productos;
* modificaciones de productos;
* consultas desconocidas;
* errores del sistema.

---

## Atención híbrida

El control de una conversación podrá alternarse libremente entre el AI Assistant y un Advisor.

La conversación nunca perderá su contexto.

El cliente nunca deberá percibir este cambio.

---

## Unified Inbox

El Dashboard deberá mostrar una bandeja unificada de conversaciones.

Los Advisors podrán identificar rápidamente:

* conversaciones pendientes;
* conversaciones asignadas;
* conversaciones atendidas por IA;
* conversaciones que requieren seguimiento.

---

## Seguimiento comercial

La plataforma deberá identificar oportunidades que requieren seguimiento.

Las oportunidades prioritarias deberán destacarse claramente.

---

## Gestión de recursos

El AI Assistant deberá poder enviar automáticamente Assets registrados por la empresa.

Ejemplos:

* fotografías;
* videos;
* fichas técnicas;
* catálogos;
* documentos PDF.

---

## Business Knowledge

Toda respuesta deberá construirse utilizando el conocimiento del negocio.

Inicialmente dicho conocimiento podrá provenir de:

* archivos Excel;
* catálogos;
* listas de precios;
* Assets;
* información de Siigo (mediante API);
* reglas comerciales.

---

## Persistencia

Toda conversación deberá conservar su historial.

Toda oportunidad deberá registrar:

* estado;
* responsable;
* historial;
* seguimiento.

---

## Configuración

El sistema deberá permitir modificar la configuración básica del AI Assistant sin modificar el código fuente.

---

# Fuera del alcance del MVP

No forman parte del MVP:

* múltiples organizaciones;
* múltiples AI Assistants;
* RAG avanzado;
* memoria semántica;
* automatizaciones complejas;
* marketplace;
* SDK;
* facturación;
* voz;
* llamadas telefónicas;
* múltiples canales simultáneos;
* generación automática de empaques personalizados desde cero.

Estas funcionalidades serán desarrolladas en versiones posteriores.

---

# Restricciones

El desarrollo deberá respetar la arquitectura definida en `04_Architecture.md`.

Toda funcionalidad deberá seguir los principios definidos en `03_Engineering_Principles_and_Standards.md`.

El MVP utilizará Telegram como canal de validación debido a las restricciones actuales de acceso a WhatsApp Cloud API.

La incorporación de WhatsApp deberá requerir únicamente un nuevo Channel Provider.

---

# Criterios de aceptación

El MVP se considerará exitoso cuando permita:

* atender automáticamente la mayoría de consultas repetitivas;
* transferir correctamente conversaciones complejas al equipo humano;
* mantener el contexto durante toda la conversación;
* reducir significativamente el tiempo de primera respuesta;
* facilitar el seguimiento de oportunidades comerciales;
* mejorar la experiencia del equipo comercial;
* demostrar una mejora medible en el proceso comercial de Amza Empaques.

---

# Definición de MVP

El MVP no representa la versión final del producto.

Representa la primera validación funcional de una plataforma de atención comercial híbrida.

Su propósito consiste en demostrar que la combinación entre Inteligencia Artificial y atención humana puede aumentar la capacidad comercial de una empresa sin incrementar proporcionalmente el tamaño de su equipo.

