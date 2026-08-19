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
        <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500 dark:bg-gray-800">
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
        className={`max-w-[75%] rounded-lg px-3 py-2 text-sm shadow-sm ${
          isCustomer
            ? "bg-white dark:bg-gray-800"
            : message.sender_role === "advisor"
              ? "bg-sky-100 dark:bg-sky-900"
              : "bg-emerald-100 dark:bg-emerald-900"
        }`}
      >
        {label && (
          <p className="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            {label}
          </p>
        )}
        {message.content_type !== "text" ? (
          <FileCard type={message.content_type} />
        ) : (
          <p
            className="whitespace-pre-wrap"
            dangerouslySetInnerHTML={{
              __html: highlightText(message.content, searchQuery ?? ""),
            }}
          />
        )}
        <p className="mt-1 text-right text-[10px] text-gray-400">{time}</p>
      </div>
    </div>
  );
}
