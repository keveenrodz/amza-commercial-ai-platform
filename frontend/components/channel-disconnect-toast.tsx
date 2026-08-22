"use client";

import { useEffect, useRef, useState } from "react";

import { CloseIcon, TelegramIcon, WhatsAppIcon } from "@/components/icons";
import { useChannelHealth } from "@/hooks/use-channel-health";

const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: "WhatsApp",
  telegram: "Telegram",
};

const CHANNEL_ICON: Record<string, typeof WhatsAppIcon> = {
  whatsapp: WhatsAppIcon,
  telegram: TelegramIcon,
};

// WhatsApp tiene un botón de acción real (ir a reconectar el QR) -- Telegram no tiene un QR ni
// una sesión que reconectar desde la app, el problema típico es que la URL pública registrada
// (ngrok en desarrollo) cambió y hay que volver a correr el script de registro a mano.
const CHANNEL_MESSAGE: Record<string, string> = {
  whatsapp: "Los clientes no recibirán respuestas hasta que se vuelva a conectar.",
  telegram:
    "El bot no está recibiendo mensajes correctamente -- puede que la URL pública registrada haya cambiado.",
};

export function ChannelDisconnectToast() {
  const { data: health } = useChannelHealth();
  // Un canal solo vuelve a notificar si se reconectó y se cayó de nuevo (una "incidencia"
  // nueva) -- cerrar el aviso no debe hacer que reaparezca en el siguiente sondeo mientras
  // sigue caído.
  const [visible, setVisible] = useState<Set<string>>(new Set());
  const notifiedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!health) return;
    // La mutación de notifiedRef vive aquí, fuera del updater de setVisible -- en Strict Mode
    // (dev) React invoca los updaters funcionales dos veces para detectar impurezas; si el ref
    // se mutaba adentro, la segunda invocación ya lo encontraba actualizado y descartaba el
    // canal, dejando "visible" vacío para siempre (bug real, encontrado al verificar en vivo).
    const newlyUnhealthy: string[] = [];
    const recovered: string[] = [];
    for (const [channel, healthy] of Object.entries(health)) {
      if (!healthy && !notifiedRef.current.has(channel)) {
        notifiedRef.current.add(channel);
        newlyUnhealthy.push(channel);
      } else if (healthy && notifiedRef.current.has(channel)) {
        notifiedRef.current.delete(channel);
        recovered.push(channel);
      }
    }
    if (newlyUnhealthy.length === 0 && recovered.length === 0) return;
    setVisible((current) => {
      const next = new Set(current);
      newlyUnhealthy.forEach((c) => next.add(c));
      recovered.forEach((c) => next.delete(c));
      return next;
    });
  }, [health]);

  const channels = Array.from(visible);
  if (channels.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex flex-col gap-2.5">
      {channels.map((channel) => {
        const Icon = CHANNEL_ICON[channel];
        return (
          <div
            key={channel}
            className="pointer-events-auto flex w-80 items-start gap-3 rounded-xl border border-line bg-surface/85 p-3.5 shadow-card backdrop-blur-sm"
          >
            {Icon && <Icon className="mt-0.5 h-5 w-5 flex-shrink-0 text-overdue" />}
            <div className="flex-1">
              <p className="font-heading text-[13px] font-bold text-ink">
                {CHANNEL_LABEL[channel] ?? channel} se desconectó
              </p>
              <p className="mt-0.5 text-xs text-ink-muted">
                {CHANNEL_MESSAGE[channel] ?? "Revisa la conexión de este canal."}
              </p>
              {channel === "whatsapp" && (
                <a
                  href="/admin"
                  className="mt-1.5 inline-block text-xs font-bold text-accent-deep hover:underline"
                >
                  Ir a Canales →
                </a>
              )}
            </div>
            <button
              onClick={() => setVisible((current) => {
                const next = new Set(current);
                next.delete(channel);
                return next;
              })}
              aria-label={`Cerrar aviso de ${CHANNEL_LABEL[channel] ?? channel}`}
              className="text-ink-faint hover:text-ink-muted"
            >
              <CloseIcon className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
