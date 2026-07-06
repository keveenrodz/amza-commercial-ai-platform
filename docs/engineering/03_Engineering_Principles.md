# 03 – Engineering Principles and Standards

## Objetivo

Este documento define los principios y estándares de ingeniería que deberán respetarse durante todo el ciclo de vida del proyecto.

Estos principios aplican independientemente de quién escriba el código.

Ya sea:

* un desarrollador humano;
* Claude Code;
* Codex;
* Cursor;
* Gemini;
* cualquier otra herramienta de desarrollo asistida por IA.

Ningún cambio podrá justificarse únicamente porque "la IA lo generó".

Toda decisión deberá cumplir los principios definidos en este documento.

---

# Filosofía de ingeniería

Nuestro objetivo no es escribir código rápidamente.

Nuestro objetivo es construir un producto que pueda mantenerse durante muchos años.

La velocidad nunca deberá comprometer:

* la arquitectura;
* la claridad;
* la mantenibilidad;
* la seguridad;
* la calidad.

Preferimos avanzar más lentamente con una base sólida que construir rápidamente una plataforma difícil de mantener.

---

# Principios fundamentales

## 1. El negocio primero

Toda decisión técnica deberá responder a una necesidad real del negocio.

Nunca incorporar tecnología únicamente solo porque es novedosa.

---

## 2. La arquitectura tiene prioridad

La arquitectura definida en `04_Architecture.md` deberá respetarse en todo momento.

No introducir atajos que comprometan el diseño del sistema.

---

## 3. Simplicidad sobre complejidad

Siempre elegir la solución más simple que resuelva correctamente el problema.

La simplicidad es una característica del producto.

---

## 4. Calidad antes que velocidad

Es preferible retrasar una funcionalidad antes que incorporar deuda técnica innecesaria.

---

## 5. El dominio nunca depende de la infraestructura

El Core representa el negocio.

Toda dependencia deberá apuntar hacia el dominio.

Nunca en sentido contrario.

---

## 6. El código debe ser fácil de eliminar

Toda funcionalidad deberá estar desacoplada.

Eliminar una característica nunca debería requerir modificar gran parte del sistema.

---

## 7. No desarrollar por anticipación

No implementar funcionalidades únicamente porque podrían ser útiles en el futuro.

Aplicar YAGNI ("You Aren't Gonna Need It").

---

## 8. Todo debe poder probarse

Si una funcionalidad no puede probarse razonablemente, su diseño deberá revisarse.

La testabilidad es un requisito de calidad.

---

## 9. Toda decisión importante debe documentarse

Cuando una decisión cambie la arquitectura, el comportamiento del sistema o la forma de trabajar, deberá quedar documentada.

---

## 10. Pensar siempre en el usuario

Toda decisión técnica deberá mejorar la experiencia del usuario final.

Nunca optimizar únicamente la comodidad del desarrollador.

---

# Cómo tomamos decisiones

Cuando existan varias alternativas válidas, se seguirán estas reglas.

## Entre dos soluciones

Elegir la más simple.

---

## Entre dos arquitecturas

Elegir la más desacoplada.

---

## Entre dos dependencias

Elegir la que agregue menos complejidad.

---

## Entre dos implementaciones

Elegir la más fácil de mantener.

---

## Entre dos optimizaciones

Elegir la que pueda medirse objetivamente.

Nunca realizar optimizaciones prematuras.

---

## Si una abstracción todavía no aporta valor

No crearla.

Toda nueva abstracción (`Protocol`, interfaz, capa intermedia) deberá justificar la existencia
de al menos dos implementaciones posibles, o representar un límite arquitectónico claro (un
puerto hacia infraestructura: base de datos, proveedor de IA, canal de mensajería). Si no
cumple ninguna de las dos condiciones, preferir una clase concreta.

---

# Estándares de código

## Python

* Python 3.12 o superior.
* Tipado completo.
* Uso de type hints en todas las funciones públicas.
* No utilizar características obsoletas.

---

## TypeScript

* Modo estricto.
* Sin uso de `any`, salvo casos excepcionalmente justificados.
* Tipos compartidos cuando sea posible.

---

## Estructura

Cada archivo deberá tener una única responsabilidad.

Si un archivo comienza a crecer de forma significativa, deberá dividirse.

No utilizar clases o módulos gigantes.

---

## Funciones

Las funciones deberán ser pequeñas, claras y enfocadas en una única tarea.

Evitar efectos secundarios innecesarios.
No usar emoticones ni caracteres especiales.

---

## Nombres

Los nombres deberán reflejar el lenguaje definido en `02_Product_Glossary.md`.

Nunca utilizar abreviaturas ambiguas ni emoticones.

---

## Comentarios

El código deberá ser suficientemente claro para minimizar la necesidad de comentarios.

Los comentarios deberán explicar el "por qué", no el "qué".
No usar emoticones ni caracteres especiales.

---

# Estándares de arquitectura

Todo acceso a sistemas externos deberá realizarse mediante Providers.

El dominio nunca dependerá de FastAPI, SQLAlchemy, Telegram, WhatsApp ni OpenRouter.

Los casos de uso nunca accederán directamente a la base de datos.

Toda persistencia deberá realizarse mediante Repositories y Unit of Work.

---

# Estándares de pruebas

Toda funcionalidad nueva deberá incluir pruebas acordes a su importancia.

Las pruebas deberán ser:

* repetibles;
* automáticas;
* fáciles de entender.

No escribir pruebas frágiles o excesivamente acopladas a la implementación.

## Regla formal de pruebas automatizadas (vigente desde spec 008)

Toda especificación que introduzca comportamiento nuevo deberá incluir pruebas automatizadas de
ese comportamiento antes de poder considerarse completa.

Cuando una especificación modifique comportamiento existente, también deberá actualizar las
pruebas afectadas.

Retomar retroactivamente las pruebas de especificaciones anteriores es deuda técnica y deberá
registrarse por separado — no bloquea el avance de especificaciones nuevas, pero tampoco se
resuelve implícitamente por omisión.

*Automated Testing: every specification introducing new behavior must include automated tests
covering that behavior before the specification is considered complete. When a specification
modifies existing behavior, the affected tests must also be updated. Retrofitting tests for
previous specifications is technical debt and shall be tracked separately.*

---

# Observabilidad

Todo comportamiento importante deberá registrarse mediante logging estructurado.

No utilizar `print()` para depuración en código productivo.

Los errores deberán proporcionar suficiente contexto para facilitar su diagnóstico.

---

# Seguridad

Nunca almacenar secretos en el código.

Toda configuración sensible deberá provenir del sistema de configuración.

Validar siempre las entradas externas.

Nunca confiar en información proveniente del usuario.

---

# Dependencias

Toda nueva dependencia deberá justificarse.

Antes de agregar una librería deberá evaluarse:

* si realmente resuelve un problema;
* si reduce el esfuerzo de mantenimiento;
* si es ampliamente utilizada;
* si tiene mantenimiento activo.

Evitar incorporar librerías para resolver problemas triviales.

---

# Documentación

Toda funcionalidad importante deberá reflejarse en la documentación correspondiente.

La documentación forma parte del producto.

No deberá considerarse una tarea opcional.
No usar emoticones ni caracteres especiales.

---

# Ingeniería asistida por IA

Las herramientas de IA son asistentes de desarrollo.

No sustituyen el criterio del equipo.

Toda contribución generada mediante IA deberá:

* revisarse;
* comprenderse;
* probarse;
* adaptarse cuando sea necesario.

Nunca aceptar código únicamente porque fue generado automáticamente.

---

# Definición de calidad

Una funcionalidad solo podrá considerarse terminada cuando:

* resuelva el problema definido;
* respete la arquitectura;
* cumpla los estándares del proyecto;
* esté probada;
* esté documentada;
* no introduzca deuda técnica innecesaria.

---

# Principio final

Cada línea de código deberá escribirse pensando que otra persona tendrá que mantenerla dentro de varios años.

La mejor ingeniería no consiste en escribir código complejo.

Consiste en construir sistemas simples, claros y confiables que permitan al negocio crecer de forma sostenible.

