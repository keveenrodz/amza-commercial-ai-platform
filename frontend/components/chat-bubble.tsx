import { FileCard } from "@/components/file-card";
import { highlightText } from "@/lib/highlight";
import type { Message } from "@/types/api";

function bubbleLabel(role: Message["sender_role"]): string | null {
  if (role === "assistant") return "IA";
  if (role === "advisor") return "Asesor"; // sin nombre específico -- ver spec 012, "Fuera de alcance"
  return null;
}

export function ChatBubble({ message, searchQuery }: { message: Message; searchQuery?: string }) {
  if (message.sender_role === "system") {
    return (
      <div className="my-2 flex justify-center">
        <span className="max-w-[70%] rounded-lg bg-surface-2 px-3 py-1.5 text-center text-[11.5px] text-ink-muted">
          {message.content}
        </span>
      </div>
    );
  }

  const isCustomer = message.sender_role === "user";
  const label = bubbleLabel(message.sender_role);
  const time = new Date(message.sent_at).toLocaleTimeString("es-CO", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex ${isCustomer ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[62%] rounded-[13px] px-3 py-2 text-[13.5px] shadow-card ${
          isCustomer
            ? "rounded-tl-[3px] bg-bubble-customer"
            : message.sender_role === "advisor"
              ? "rounded-tr-[3px] bg-bubble-advisor"
              : "rounded-tr-[3px] bg-bubble-agent"
        }`}
      >
        {label && (
          <p className="mb-0.5 font-heading text-[10px] font-extrabold uppercase tracking-wide text-info">
            {label}
          </p>
        )}
        {message.content_type !== "text" ? (
          <FileCard type={message.content_type} />
        ) : (
          <p
            className="whitespace-pre-wrap text-ink"
            dangerouslySetInnerHTML={{
              __html: highlightText(message.content, searchQuery ?? ""),
            }}
          />
        )}
        <p className="mt-1 text-right text-[10.5px] tabular-nums text-ink-faint">{time}</p>
      </div>
    </div>
  );
}
