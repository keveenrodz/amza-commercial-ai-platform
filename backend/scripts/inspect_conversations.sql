-- Consultas de solo lectura para revisar manualmente lo que llegó por Telegram durante pruebas
-- locales. Abrir contra backend/data/amza.db (consola SQL de tu IDE, o `sqlite3 data/amza.db`).

-- Contactos que han escrito: nombre de Telegram y su chat_id (NO es un teléfono, ver nota abajo).
SELECT
    display_name,
    external_id AS telegram_chat_id,
    channel_type,
    status,
    created_at
FROM contacts
ORDER BY created_at DESC;

-- Conversación completa de cada contacto, en orden cronológico.
SELECT
    c.display_name,
    m.sender_role,
    m.content,
    m.sent_at
FROM messages m
JOIN conversations conv ON conv.id = m.conversation_id
JOIN opportunities o ON o.id = conv.opportunity_id
JOIN contacts c ON c.id = o.contact_id
ORDER BY m.sent_at;
