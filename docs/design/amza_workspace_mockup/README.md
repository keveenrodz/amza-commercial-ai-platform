# Amza Workspace — mockup de rediseño (pre-spec 011)

Mockup HTML interactivo (sin backend) del rediseño propuesto del Advisor Workspace: barra lateral
de navegación, panel de chat estilo WhatsApp Web, panel de información del cliente, tema
claro/oscuro, y las demás piezas discutidas antes de escribir la spec 011 formal.

No es código de producto — es un artefacto de discusión de diseño para validar la dirección
visual e interacción antes de comprometerla a una spec. Cuando se apruebe, la spec 011 (y las
siguientes del rediseño) implementan esto en `frontend/` de verdad.

## Ver el mockup

Abrir `amza_workspace_mockup.html` directamente en un navegador (no requiere servidor).

## Editar

- `template.html` — estructura, estilos y lógica (con placeholders `__LOGO_B64__`, `__FONT_B64__`,
  `__DATA_JSON__`).
- `data.json` — datos de ejemplo (contactos, mensajes, etiquetas, notas, seguimientos).
- `manrope.woff2` — tipografía de marca (Manrope, usada para la barra lateral y encabezados).

Después de editar `template.html` o `data.json`, reconstruir con:

```bash
python docs/design/amza_workspace_mockup/build.py
```

Esto regenera `amza_workspace_mockup.html` incrustando el logo (`amza-logo.png` en la raíz del
repo) y la tipografía como `data:` URIs, para que el archivo resultante sea autocontenido.
