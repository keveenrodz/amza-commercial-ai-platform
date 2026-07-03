# MVP Specification – 001 Project Setup

## Objetivo

Crear la estructura inicial del proyecto respetando completamente la arquitectura definida en la documentación oficial.

Este documento únicamente define la creación del proyecto.

No deberán implementarse funcionalidades de negocio.

No deberán implementarse integraciones.

No deberán implementarse pantallas.

El resultado esperado es un proyecto limpio, compilable y preparado para comenzar el desarrollo.

---

# Objetivos

Al finalizar esta tarea deberá existir un proyecto completamente inicializado con:

* Backend
* Frontend
* Docker
* Configuración
* Calidad de código
* Testing
* CI básica

Sin implementar ninguna funcionalidad del negocio.

---

# Tipo de repositorio

El proyecto utilizará un **Monorepo**.

Toda la plataforma deberá mantenerse dentro de un único repositorio Git.

---

# Estructura esperada

```text
project-root/

backend/

frontend/

docs/

specifications/

docker/

scripts/

.github/

.env.example

.gitignore

README.md

Makefile
```

No crear directorios adicionales salvo que exista una razón claramente justificada.

---

# Backend

Crear un proyecto utilizando:

* Python 3.12
* FastAPI
* SQLAlchemy 2.x
* Alembic
* Pydantic v2
* Pydantic Settings

Crear únicamente la estructura base.

No crear endpoints.

No crear modelos.

No crear lógica de negocio.

---

# Frontend

Crear un proyecto utilizando:

* Next.js 15
* React 19
* TypeScript
* Tailwind CSS
* shadcn/ui

Crear únicamente la estructura inicial.

No crear páginas funcionales.

No implementar componentes de negocio.

---

# Docker

Crear los archivos necesarios para ejecutar el proyecto localmente mediante Docker Compose.

El objetivo es facilitar el desarrollo.

No optimizar todavía para producción.

---

# Git

Inicializar el repositorio.

Agregar un `.gitignore` adecuado para Python, Node.js y Docker.

---

# Calidad

Configurar desde el primer día:

Backend:

* Ruff
* MyPy
* Pre-commit

Frontend:

* ESLint
* Prettier

Todas las herramientas deberán ejecutarse correctamente antes de considerar finalizada la tarea.

---

# Testing

Configurar:

Backend:

* Pytest
* pytest-asyncio

Frontend:

* Vitest
* Playwright

No escribir todavía pruebas funcionales.

Únicamente dejar preparado el entorno.

---

# Integración Continua

Crear un workflow básico de GitHub Actions que ejecute:

* instalación de dependencias;
* lint;
* pruebas básicas.

---

# Variables de entorno

Crear un archivo `.env.example`.

Nunca incluir secretos.

Nunca incluir credenciales reales ni llaves.

---

# README

Crear un README inicial con:

* descripción del proyecto;
* requisitos;
* instalación;
* ejecución local;
* estructura general del repositorio.

---

# Makefile

Crear un Makefile con comandos básicos.

Ejemplos:

* instalar
* ejecutar backend
* ejecutar frontend
* ejecutar pruebas
* ejecutar lint
* ejecutar formateo
* levantar Docker

Todos los comandos deberán funcionar correctamente.

---

# Qué NO debe hacerse

Durante esta tarea queda explícitamente prohibido:

* crear endpoints;
* crear modelos del dominio;
* crear tablas;
* crear Providers;
* crear AI Assistants;
* crear Runtime;
* crear Dashboard funcional;
* crear autenticación;
* crear integraciones;
* crear lógica de negocio.

El objetivo es exclusivamente preparar la base del proyecto.

---

# Definición de terminado

La tarea se considerará terminada cuando:

* el repositorio compile correctamente;
* backend y frontend puedan iniciarse localmente;
* Docker funcione;
* las herramientas de calidad estén configuradas;
* las pruebas puedan ejecutarse;
* el proyecto respete la estructura aprobada.

No se evaluará ninguna funcionalidad de negocio.

---

# Principio fundamental

El propósito de esta tarea no es construir la plataforma.

El propósito consiste en construir una base sólida sobre la cual desarrollar el resto del proyecto de forma ordenada y mantenible.

