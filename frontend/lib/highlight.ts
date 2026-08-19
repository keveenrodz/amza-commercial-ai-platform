function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Escapa el texto ANTES de envolver coincidencias en <mark> -- el <mark> es el único HTML que
// esta función puede producir, nunca contenido del mensaje en sí (evita XSS vía
// dangerouslySetInnerHTML en quien la consuma).
export function highlightText(text: string, query: string): string {
  const escaped = escapeHtml(text);
  const trimmed = query.trim();
  if (!trimmed) return escaped;
  const pattern = new RegExp(`(${escapeRegExp(trimmed)})`, "ig");
  return escaped.replace(pattern, "<mark>$1</mark>");
}
