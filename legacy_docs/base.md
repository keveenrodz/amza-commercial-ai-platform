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
_____________________________-

Tengo una empresa llamada Amza empaques, actualmente manejamos 3 canales (whatsapp, instagram y facebook messenger), y se responden manualmente uno a uno, sin embargo nos demoramos demasiado respondiendo más de 200 mensajes al dia, o a veces ni siquiera alcanzamos a responderlos todos, porque varios clientes piden cotizaciones de empaques personalizados y esto toca calcularlo y hacerlo, algo que toma más de 30 minutos, como también cuando piden fotos o videos de los empaques, y va consumiendo más tiempo, también pasa que se nos es demasiado dificil hacerle seguimiento a clientes a los cuales ya se les enviaron cotizaciones, y por todo esto perdemos ventas. Entonces por eso pensamos en construir una herramienta como la que te mencioné, que facilite responder a los mensajes, y que si piden cotizacion o cosas mas elaboradas entonces pasen a ser atendidos por humano, y que pueda volver a ser atendidos por la IA (que se pueda intercalar la comunicacion entre ia y humano), y que si se requiere atencion a humano que se notifique en la plataforma y que muestre cuales, si es solo consulta de productos con sus precios y fotos normales entonces ahi si que los atienda un agente de IA. Todo esto para que el proceso no sea un cuello botella sino que ayude a captar más clientes y cerrarlos. Adicionalmente la base de conocimientos esta entre archivos de excel , aplicar formulas para personaziados, y que use imagenes d elos productos apra enviarlos (enviar assets), y conectores via api a Siigo (inventario y cotizaciones), como también al CRM (pendiente de seleccionar). Los que la van a usar son los propios empleados de Amza, que actualmente son 2, ninguno técnico, y yo no cuento poruqe aunque si soy tecnico (senior data scientist) solo ayudo en cosas, ya que la empresa es de mi madre.

¿Cuál es el producto principal de Amza?: Son empaques ecologicos y biodegradables, Una empresa que elabora y distribuye empaques biodegradables, sostenibles y compostables fabricados con materiales 100% sostenibles ¿Cuántos mensajes llegan aproximadamente por día?: en terminos de contactos llegan más de 200, y mensajes varia de acuerdo a la conversacion que se tenga con cada contacto. ¿Cuántas cotizaciones personalizadas hacen por día?, al rededor del 70% de los clientes buscan cotizaciones. Aqui debo de hacer una aclaración, y es que personalziado puede ser 2 cosas, la priemra es personalziar una bolsa o vaso de medida estandar que ya se maneja y se personaliza con impresion, y la segunda personalziacion es hacer un empaque desde cero, osea con diseo y medidas indicadas por el cliente, como también modificar las medidas de algun empaque que ya manejamos, como por ejemplo cambiarle las dimensiones a una bolsa. Entonces, si es la priemra el agente de IA puede responder sin pasar al humano, si es la segunda ahi si debe pasar al humano (por el momento, ya que la idea posterior es que también lo haga el agente ia). Y ya si son preguntas que el agente no puede responder entonces pasa al humano. ¿Cuánto tarda una cotización promedio?: actualmente nos tardamos entre 30 min a 2 horas ¿Qué porcentaje de los mensajes son preguntas repetidas?: los ejemplos que ponen siempre lo hacen, entonces el 90% de los clientes los preguntan ¿Cuántos productos tienen?: al rededor de 300 productos ¿Las imágenes ya están organizadas?: no todas, aun falta por organizar y tomar, pero ay se tienen muchas ¿Cómo saben hoy que un cliente necesita seguimiento?: poruqe se le envio cotizacion de alto valor o es un cliente que conocemos a priori que es relevante (por una empresa conocida o algo), pero la mayoria de las veces se nos pierden ¿Cuál CRM piensas usar?, usabamos RD Station CRM pero por este desorden lo dejamos de pagar, por el momento sigue pendiente de adquirir. ¿Cómo medirías el éxito?: por cerrar ventas, reducir pérdidas, y conformidad del cliente ¿Qué es lo peor que podría hacer la IA?: todas las que mencionas, como Dar un precio incorrecto, Prometer algo que no existe, Inventar inventario, Dar una cotización errónea. ¿Trabajan al mismo tiempo?: si, trabajan en la misma oficina, mismo horario, y ambos deberian de ver la plataforma, y se pueden intercalar en responde rlos mensajes que necesiten de respuesta humana. Algo importante es que los empleados si la plataforma les dice que un contacto de whatsapp requiere de atencion humana entonces ellos pueden responderle desde la app de whatsapp directamente (si es que esto es posible debido al api de meta whatsapp) ¿Qué debería pasar cuando llegan 50 conversaciones al mismo tiempo?: la idea seria responder por bloques, y se va creando cola, aunque la idea no es que el cliente espere mucho tiempo, es responder lo más rapido posible. El proyecto se considerará un éxito si permite hacer todo lo que buscamos, permite hacerle monitoreo, y que veamos los resultados tangibles como cierre de ventas en el profit.

¿Qué quieres que sienta un cliente cuando escriba?: seria que sientan "Nunca me di cuenta de cuándo respondió la IA y cuándo respondió una persona.", "Me atendieron mejor que otras empresas." y "Fueron super eficientes y entendieron muy bien lo que estaba buscando" ¿Qué quieres que sienta la asesora cuando llegue al trabajo?: "Sé exactamente a quién debo responder." y sé que cotización debo de hacer, aunque también gustaria tener una seccion de clientes favoritos, para tener prioridad y hacer seguimientos manuelaes en caso de que se necesiten. ¿Qué prefieres perder?: Que la IA deje de responder, pero que informe el fallo para que los empleados empiecen a responder manualmente ¿Qué frase te gustaría escuchar?: "Gracias a esta plataforma pudimos duplicar las ventas sin duplicar el equipo."

______________________________________________________________________________________-


00_Vision_and_Product_Principles.md

Describe por qué existe el producto.

↓

01_Business_Validation.md

Describe exactamente cómo validaremos el MVP dentro de Amza.

↓

02_Engineering_Principles.md

Reglas de ingeniería.

↓

03_Architecture.md

La arquitectura que ya construimos.

↓

04_Roadmap.md

La evolución del producto.

↓

05_Product_Specification.md

Qué construiremos en esta primera iteración.



Sprint 1

Objetivo:

Crear el esqueleto del proyecto.

Documento:

010_Backend_Foundation.md

Resultado esperado:

backend/

src/

commercial_ai_platform/

core/

domain/

application/

infrastructure/

api/

tests/

Nada más.

Sin IA.

Sin Telegram.

Sin Dashboard.

Sprint 2

Crear el modelo del dominio.

Sprint 3

Persistencia.

Sprint 4

API.

Sprint 5

Telegram.

Sprint 6

AI Assistant.

Sprint 7

Dashboard.



Hay otra cosa que quiero proponerte

Creo que deberíamos trabajar como si yo fuera el Software Architect y Claude Code fuera el Senior Software Engineer.

Es decir:

Yo:

diseño;
reviso;
cuestiono;
mejoro;
detecto problemas;
propongo cambios.

Claude:

implementa;
refactoriza;
genera código;
crea tests;
ejecuta tareas repetitivas.

Creo que esa combinación va a dar un resultado muchísimo mejor que intentar que una sola IA haga ambas cosas.


Hay una última recomendación que quiero hacerte

Creo que deberíamos congelar la documentación principal.

Es decir:

docs/

queda prácticamente congelada.

Solo cambia si:

aparece un nuevo requisito de negocio;
encontramos un error arquitectónico;
decidimos cambiar una decisión importante (registrándola mediante un ADR).

Mientras tanto, todo el trabajo ocurre en specifications/ y en el código.

Eso evita que la documentación y la implementación se desincronicen.
