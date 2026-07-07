# Dar acceso a un nuevo InternalUser (Advisor o Administrator)

Referencia operativa, no una spec — el diseño completo está en
`specifications/MVP/008_Security_and_Identity.md`. Esto es el "cómo hacerlo", no el "por qué".

## Los dos controles de acceso son independientes

Es fácil confundirlos porque hoy, en la práctica, hace falta tocar los dos. Pero son cosas
distintas:

1. **`InternalUser` en nuestra base de datos** — decide quién tiene acceso a la plataforma.
   Se gestiona con `scripts/create_user.py`, desde terminal. **Nunca requiere entrar a Google.**
2. **Lista de "usuarios de prueba" en Google Cloud Console** — restricción que impone *Google*,
   no nosotros, mientras la app OAuth siga en estado **Pruebas (Testing)**. Bloquea a cualquier
   cuenta que no esté en esa lista *antes* de que llegue a nuestro backend.

El punto 2 desaparece por completo si publicas la app (ver más abajo). El punto 1 siempre existe
— es correcto que exista, es nuestro único control de acceso real (ver "Principio arquitectónico"
en spec 008).

---

## Paso 1 (siempre necesario) — crear el `InternalUser`

```bash
cd backend
conda activate amza-commercial-ai-platform
python scripts/create_user.py --org <slug-organizacion> --email <email-de-google> \
    --name "Nombre Completo" --role advisor    # o --role administrator
```

Ejemplo real:

```bash
python scripts/create_user.py --org amza-empaques --email juan@gmail.com \
    --name "Juan Pérez" --role advisor
```

Sin contraseña que definir ni comunicar — la próxima vez que esa persona inicie sesión con esa
cuenta de Google, el sistema ya la reconoce. Si el email ya existe (sin distinguir mayúsculas),
el script rechaza la creación con un mensaje claro.

**Este paso es siempre necesario, publiques o no la app.**

---

## Paso 2 (solo si la app sigue en modo Pruebas) — agregar como test user en Google

Mientras la pantalla de consentimiento OAuth esté en estado **Pruebas**, cada persona nueva
también necesita que agregues su email en Google Cloud Console:

1. https://console.cloud.google.com/apis/credentials/consent (selecciona el proyecto
   `amza-commercial-ai-platform`)
2. Sección **"Usuarios de prueba"** → **"+ Añadir usuarios"**
3. Agrega el mismo email que usaste en el Paso 1
4. Guardar

Sin este paso, Google le muestra a esa persona un error de "esta app no está verificada" y ni
siquiera llega a nuestro backend — el Paso 1 por sí solo no basta mientras la app siga en Pruebas.

**Límite del modo Pruebas:** máximo 100 usuarios de prueba, y hay que repetir este paso por cada
persona nueva.

---

## Alternativa recomendada — publicar la app (elimina el Paso 2 para siempre)

Como la app solo pide scopes básicos y no sensibles (`openid`, `email`, `profile`), Google permite
publicarla sin ningún proceso de verificación:

1. https://console.cloud.google.com/apis/credentials/consent
2. Botón **"Publicar aplicación"** → confirmar
3. Listo — el estado pasa de "Pruebas" a "En producción"

**Qué cambia:**
- Cualquier cuenta de Google puede pasar la pantalla de consentimiento — el Paso 2 desaparece
  por completo. Dar acceso a alguien nuevo queda reducido exclusivamente al Paso 1.
- La persona verá una pantalla de advertencia de Google ("Google no verificó esta app") antes de
  continuar — click en **"Avanzado"** → **"Ir a Amza Commercial AI Platform (no seguro)"**. Es
  molesto pero no bloquea nada; sigue siendo el mismo flujo OAuth real, sin ningún riesgo
  adicional para el usuario.
- Se puede revertir a Pruebas en cualquier momento desde la misma pantalla si algún día se
  necesita restringir de nuevo.

**Cuándo pasar a verificación real (opcional, más adelante):** solo si algún día molesta la
pantalla de advertencia para usuarios externos a la empresa, o si se agregan scopes sensibles.
Para el uso interno actual (un puñado de asesores conocidos) no aporta nada — es trabajo
adicional sin beneficio real hoy.

---

## Quitarle acceso a alguien

No se borra el `InternalUser` — se desactiva, para conservar el registro:

```bash
cd backend
python -c "
import asyncio, sqlite3
conn = sqlite3.connect('data/amza.db')
conn.execute(\"UPDATE internal_users SET status = 'inactive' WHERE email = 'juan@gmail.com'\")
conn.commit()
print('desactivado')
"
```

Efecto inmediato, no hay que esperar a que expire ninguna sesión — `get_current_user()` vuelve a
consultar la BD en cada request (spec 008, sección 4). Si la persona tenía una sesión abierta,
pierde acceso en la siguiente petición, sin importar cuánto le quede al JWT.
