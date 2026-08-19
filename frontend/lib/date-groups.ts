import type { Message } from "@/types/api";

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function dayLabel(date: Date): string {
  const diffDays = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86_400_000);
  if (diffDays === 0) return "Hoy";
  if (diffDays === 1) return "Ayer";
  return date.toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
}

export interface MessageDayGroup {
  label: string;
  messages: Message[];
}

// Puramente de presentación -- no cambia ningún dato, solo cómo se agrupa lo que ya llegó.
export function groupMessagesByDay(messages: Message[]): MessageDayGroup[] {
  const groups: MessageDayGroup[] = [];
  for (const message of messages) {
    const label = dayLabel(new Date(message.sent_at));
    const last = groups[groups.length - 1];
    if (last && last.label === label) {
      last.messages.push(message);
    } else {
      groups.push({ label, messages: [message] });
    }
  }
  return groups;
}
