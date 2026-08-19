"use client";

import { useEffect, useRef, useState } from "react";

import { SearchIcon } from "@/components/icons";

// Mismo set curado y misma lógica de "frecuentes" ya validados en el mockup
// (docs/design/amza_workspace_mockup/template.html, EMOJI_DATA/getFrequentEmojis) -- portado a
// React, no rediseñado.
const EMOJI_DATA: { e: string; k: string }[] = [
  { e: "😀", k: "feliz sonrisa contento" },
  { e: "😊", k: "sonrisa amable contento" },
  { e: "🙂", k: "sonrisa leve" },
  { e: "😉", k: "guiño" },
  { e: "😅", k: "alivio nervioso" },
  { e: "😂", k: "risa gracioso" },
  { e: "😍", k: "encantado enamorado" },
  { e: "🥳", k: "fiesta celebracion" },
  { e: "😴", k: "sueño cansado" },
  { e: "😕", k: "confundido duda" },
  { e: "😬", k: "incomodo nervioso" },
  { e: "😢", k: "triste" },
  { e: "😡", k: "enojado molesto" },
  { e: "🤔", k: "pensando duda" },
  { e: "🙏", k: "gracias por favor" },
  { e: "👍", k: "bien ok aprobado" },
  { e: "👎", k: "mal no aprobado" },
  { e: "👋", k: "hola saludo adios" },
  { e: "🤝", k: "trato acuerdo negocio" },
  { e: "✍️", k: "firma escribir" },
  { e: "👏", k: "aplauso felicidades" },
  { e: "💪", k: "fuerza animo" },
  { e: "🖐️", k: "espera alto mano" },
  { e: "❤️", k: "amor corazon" },
  { e: "⭐", k: "estrella favorito" },
  { e: "🔥", k: "fuego genial" },
  { e: "🎉", k: "celebracion fiesta" },
  { e: "✅", k: "listo aprobado confirmado" },
  { e: "❌", k: "no cancelado rechazado" },
  { e: "⚠️", k: "atencion alerta cuidado" },
  { e: "❓", k: "pregunta duda" },
  { e: "❗", k: "importante atencion" },
  { e: "⏰", k: "hora tiempo recordatorio" },
  { e: "📅", k: "fecha calendario cita" },
  { e: "⌛", k: "espera tiempo" },
  { e: "📦", k: "caja pedido paquete empaque" },
  { e: "🚚", k: "envio entrega camion" },
  { e: "🏭", k: "fabrica planta" },
  { e: "💰", k: "dinero pago precio" },
  { e: "💳", k: "pago tarjeta factura" },
  { e: "🧾", k: "factura recibo cotizacion" },
  { e: "📄", k: "documento archivo pdf" },
  { e: "📎", k: "adjunto archivo" },
  { e: "🖼️", k: "imagen foto" },
  { e: "📸", k: "foto camara" },
  { e: "🎥", k: "video" },
  { e: "📞", k: "llamada telefono" },
  { e: "💬", k: "mensaje chat" },
  { e: "📧", k: "correo email" },
  { e: "📍", k: "ubicacion direccion" },
  { e: "🚀", k: "rapido lanzamiento" },
  { e: "♻️", k: "reciclaje" },
  { e: "🌱", k: "planta sostenible" },
  { e: "💡", k: "idea sugerencia" },
  { e: "🔧", k: "ajuste soporte tecnico" },
  { e: "🛒", k: "compra pedido" },
  { e: "🎁", k: "regalo promocion" },
  { e: "💯", k: "perfecto totalmente" },
  { e: "👌", k: "perfecto ok" },
  { e: "🙌", k: "genial celebracion manos" },
  { e: "😎", k: "genial cool" },
  { e: "🤗", k: "abrazo bienvenida" },
];

const STORAGE_KEY = "amza-emoji-freq";
const DEFAULT_FREQUENT = ["👍", "✅", "🙏"];

function getUsage(): Record<string, number> {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "{}") as Record<
      string,
      number
    >;
  } catch {
    return {};
  }
}

function bumpUsage(emoji: string) {
  const usage = getUsage();
  usage[emoji] = (usage[emoji] ?? 0) + 1;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(usage));
  } catch {
    // localStorage no disponible (modo privado, etc.) -- el picker sigue funcionando, solo sin
    // persistir frecuencia entre sesiones.
  }
}

function getFrequent(): string[] {
  const usage = getUsage();
  const used = Object.keys(usage).sort((a, b) => usage[b] - usage[a]);
  const out = used.slice(0, 3);
  for (const emoji of DEFAULT_FREQUENT) {
    if (out.length >= 3) break;
    if (!out.includes(emoji)) out.push(emoji);
  }
  return out;
}

export function EmojiPicker({
  onPick,
  onClose,
}: {
  onPick: (emoji: string) => void;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [frequent, setFrequent] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFrequent(getFrequent());
  }, []);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [onClose]);

  function pick(emoji: string) {
    bumpUsage(emoji);
    setFrequent(getFrequent());
    onPick(emoji);
  }

  const trimmed = query.trim().toLowerCase();
  const results = trimmed ? EMOJI_DATA.filter((d) => d.k.includes(trimmed)) : EMOJI_DATA;

  return (
    <div
      ref={containerRef}
      className="absolute bottom-full left-0 z-30 mb-2 w-72 rounded-xl border border-line bg-surface p-2.5 shadow-card"
    >
      <div className="mb-2 flex items-center gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1.5">
        <SearchIcon className="h-3.5 w-3.5 flex-shrink-0 text-ink-faint" />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar emoji"
          className="w-full bg-transparent text-xs outline-none placeholder:text-ink-faint"
        />
      </div>

      {!trimmed && (
        <div className="mb-2 border-b border-line pb-2">
          <p className="mb-1 font-heading text-[10px] uppercase tracking-wide text-ink-faint">
            Frecuentes
          </p>
          <div className="grid grid-cols-8 gap-0.5">
            {frequent.map((emoji) => (
              <button
                key={emoji}
                type="button"
                onClick={() => pick(emoji)}
                className="rounded p-1 text-lg leading-none hover:bg-surface-2"
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid max-h-40 grid-cols-8 gap-0.5 overflow-y-auto">
        {results.length === 0 ? (
          <p className="col-span-8 py-3 text-center text-xs text-ink-faint">Sin resultados</p>
        ) : (
          results.map((d) => (
            <button
              key={d.e}
              type="button"
              onClick={() => pick(d.e)}
              className="rounded p-1 text-lg leading-none hover:bg-surface-2"
            >
              {d.e}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
