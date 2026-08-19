import { ClockIcon, TelegramIcon, WhatsAppIcon } from "@/components/icons";
import type { FollowUp, Opportunity } from "@/types/api";

export function ChannelChip({ channelType }: { channelType: string }) {
  const isWhatsApp = channelType === "whatsapp";
  const Icon = isWhatsApp ? WhatsAppIcon : TelegramIcon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
        isWhatsApp
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
      }`}
    >
      <Icon className="h-2.5 w-2.5" />
      {isWhatsApp ? "WhatsApp" : "Telegram"}
    </span>
  );
}

export function StatusChip({
  opportunity,
  currentUserId,
}: {
  opportunity: Opportunity;
  currentUserId: string;
}) {
  if (opportunity.attention_mode === "ai") {
    return (
      <span className="inline-flex items-center rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-semibold text-sky-800 dark:bg-sky-900 dark:text-sky-200">
        IA
      </span>
    );
  }
  if (opportunity.assigned_advisor_id === currentUserId) {
    return (
      <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
        Mía
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
      Asignada
    </span>
  );
}

export function FollowUpChip({ followUp }: { followUp: FollowUp }) {
  const overdue = new Date(followUp.due_at) < new Date();
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
        overdue
          ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
          : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
      }`}
    >
      <ClockIcon className="h-2.5 w-2.5" />
      {overdue ? "Vencido" : "Seguimiento"}
    </span>
  );
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}
