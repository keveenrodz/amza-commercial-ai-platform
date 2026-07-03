# 01 – Business Validation

## Propósito

Este documento define el primer caso de uso real de la plataforma y establece cómo se validará que el producto genera valor para el negocio.

La primera empresa donde se implementará la plataforma será **Amza Empaques**.

El objetivo de esta implementación no es únicamente validar la tecnología.

El objetivo principal es demostrar que la plataforma mejora el proceso comercial de la empresa y permite aumentar la capacidad de atención sin incrementar el tamaño del equipo.

---

# Contexto del negocio

Amza Empaques es una empresa dedicada a la fabricación y distribución de empaques ecológicos, biodegradables y compostables.

Su proceso comercial depende principalmente de conversaciones iniciadas por clientes a través de canales digitales.

Actualmente la empresa recibe más de 200 nuevos contactos diarios provenientes de diferentes canales.

La atención es realizada manualmente por un equipo de dos asesoras comerciales.

A medida que aumenta el número de conversaciones, también aumenta la probabilidad de:

* responder tarde;
* olvidar clientes;
* perder oportunidades comerciales;
* retrasar cotizaciones;
* dejar seguimientos sin realizar.

El principal cuello de botella del negocio no es la generación de clientes potenciales.

El cuello de botella es la capacidad humana para atenderlos.

---

# Problema principal

Hoy gran parte del tiempo de las asesoras se consume en actividades repetitivas.

Entre ellas:

* responder preguntas frecuentes;
* enviar fotografías de productos;
* compartir fichas técnicas;
* consultar precios;
* explicar materiales y productos;
* responder preguntas sobre envíos;
* buscar información del catálogo.

Como consecuencia:

* las cotizaciones complejas se retrasan;
* el seguimiento comercial disminuye;
* algunos clientes abandonan el proceso antes de comprar.

---

# Hipótesis

Si la plataforma responde automáticamente todas las consultas repetitivas y transfiere únicamente los casos que requieren criterio humano, entonces el equipo podrá atender un mayor número de clientes, realizar más seguimientos y aumentar las ventas sin aumentar el número de empleados.

---

# Objetivo del piloto

Validar que una atención híbrida entre Inteligencia Artificial y asesores comerciales mejora significativamente el proceso comercial de Amza Empaques.

El piloto deberá demostrar que la plataforma puede convertirse en el centro operativo de la atención comercial.

---

# Qué validaremos

Durante esta primera implementación validaremos los siguientes escenarios.

## Atención automática

La IA deberá responder automáticamente consultas relacionadas con:

* catálogo de productos;
* materiales;
* precios estándar;
* cantidades mínimas y descuentos;
* tiempos de fabricación;
* tiempos de entrega;
* medios de pago;
* envíos;
* preguntas frecuentes.

---

## Envío de recursos

La plataforma deberá poder enviar automáticamente:

* fotografías;
* videos;
* fichas técnicas;
* archivos PDF;
* documentos comerciales;
* otros recursos previamente registrados.

---

## Cotizaciones estándar

Cuando un cliente solicite personalizar un producto existente únicamente mediante impresión, la plataforma deberá generar la cotización automáticamente utilizando las reglas definidas por la empresa. Como también generar cotización sin personalizaciones.

---

## Escalamiento a humano

La conversación deberá pasar automáticamente a un asesor cuando ocurra cualquiera de las siguientes situaciones:

* desarrollo de un empaque completamente nuevo;
* modificación de dimensiones de un producto existente;
* solicitudes especiales;
* dudas que la IA no pueda responder con suficiente confianza;
* errores internos de la plataforma;
* solicitud explícita del cliente para hablar con una persona.

La prioridad siempre será evitar respuestas incorrectas.

---

## Atención híbrida

Una conversación podrá cambiar entre IA y humano tantas veces como sea necesario.

El cliente nunca deberá percibir ese cambio.

La plataforma deberá mantener el contexto completo durante toda la conversación.

---

## Seguimiento comercial

La plataforma deberá identificar conversaciones que requieren seguimiento posterior.

Ejemplos:

* cotizaciones enviadas;
* clientes estratégicos;
* clientes con alto potencial;
* conversaciones pendientes.

Estas conversaciones deberán aparecer claramente identificadas para el equipo comercial.

---

## Clientes prioritarios

La plataforma deberá permitir marcar clientes importantes.

Estos clientes deberán aparecer destacados dentro del Dashboard y facilitar su seguimiento.

---

# Qué NO validaremos

Durante el piloto no se implementarán funcionalidades que no sean necesarias para validar el negocio.

Entre ellas:

* múltiples empresas;
* marketplace;
* facturación;
* automatizaciones complejas;
* flujos empresariales avanzados;
* RAG avanzado;
* múltiples modelos de IA;
* agentes especializados;
* voz;
* llamadas telefónicas;
* análisis predictivo.

Estas capacidades forman parte del Roadmap, pero no del piloto.

---

# Indicadores de éxito

El piloto se considerará exitoso cuando se cumplan la mayoría de los siguientes objetivos.

## Atención

La mayoría de las consultas repetitivas deberán resolverse sin intervención humana.

---

## Tiempo de respuesta

El tiempo de primera respuesta deberá reducirse significativamente respecto al proceso manual.

---

## Cotizaciones

Las cotizaciones estándar deberán generarse automáticamente.

Las cotizaciones complejas deberán llegar rápidamente al asesor correspondiente.

---

## Seguimiento

El equipo deberá conocer diariamente qué clientes requieren seguimiento.

Ninguna cotización importante deberá perderse por falta de control.

---

## Experiencia del cliente

El cliente deberá percibir una atención rápida, consistente y profesional.

Idealmente no deberá distinguir cuándo responde una persona y cuándo responde la IA.

---

## Equipo comercial

Las asesoras deberán dedicar menos tiempo a tareas repetitivas y más tiempo a actividades que generen ventas.

La plataforma deberá convertirse en una herramienta de apoyo, no en una carga adicional.

---

## Negocio

El principal indicador de éxito será demostrar una mejora medible en el proceso comercial.

Idealmente:

* más clientes atendidos;
* mayor velocidad de respuesta;
* mejor seguimiento;
* incremento en la conversión de ventas.

---

# Restricciones del piloto

El desarrollo deberá adaptarse a las limitaciones actuales del proyecto.

## Canales

La arquitectura será multicanal.

Sin embargo, debido a que la integración con WhatsApp Cloud API aún no está disponible, el primer canal implementado será Telegram.

Telegram se utilizará exclusivamente como entorno de desarrollo y validación funcional.

Una vez la integración oficial con WhatsApp esté disponible, deberá incorporarse mediante un nuevo adaptador sin modificar el Core del sistema.

---

## Integraciones

Durante el piloto se priorizarán únicamente las integraciones necesarias para demostrar el valor del producto.

Inicialmente se contemplan:

* OpenRouter (LLM)
* Telegram
* Siigo (consulta de inventario y apoyo a cotizaciones, según las APIs disponibles)

La integración con un CRM quedará preparada desde la arquitectura, pero su implementación dependerá de la herramienta seleccionada posteriormente.

---

# Criterio para finalizar el piloto

El piloto se considerará finalizado cuando el equipo de Amza pueda utilizar la plataforma durante su operación diaria y confirme que:

* mejora el proceso de atención;
* reduce el trabajo repetitivo;
* facilita el seguimiento de clientes;
* disminuye el riesgo de perder oportunidades comerciales;
* aporta valor real al negocio.

La validación del piloto será realizada por los usuarios finales del sistema y por los indicadores de negocio definidos en este documento.

---

# Principio fundamental

El objetivo del piloto no es demostrar que la Inteligencia Artificial puede responder mensajes.

El objetivo es demostrar que una plataforma de atención comercial híbrida puede ayudar a una empresa a vender más, atender mejor y crecer sin aumentar proporcionalmente su equipo comercial.

