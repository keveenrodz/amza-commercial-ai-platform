import { ClockIcon, TelegramIcon, WhatsAppIcon } from "@/components/icons";
import type { FollowUp, Opportunity } from "@/types/api";

export function ChannelChip({ channelType }: { channelType: string }) {
  const isWhatsApp = channelType === "whatsapp";
  const Icon = isWhatsApp ? WhatsAppIcon : TelegramIcon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide ${
        isWhatsApp ? "bg-whatsapp-soft text-whatsapp" : "bg-info-soft text-info"
      }`}
    >
      <Icon className="h-[9px] w-[9px]" />
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
      <span className="inline-flex items-center rounded-full bg-info-soft px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide text-info">
        IA
      </span>
    );
  }
  if (opportunity.assigned_advisor_id === currentUserId) {
    return (
      <span className="inline-flex items-center rounded-full bg-accent-soft px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide text-accent-deep">
        Mía
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide text-ink">
      <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent" />
      Asignada
    </span>
  );
}

export function FollowUpChip({ followUp }: { followUp: FollowUp }) {
  const overdue = new Date(followUp.due_at) < new Date();
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide ${
        overdue ? "bg-overdue-soft text-overdue" : "bg-warn-soft text-warn"
      }`}
    >
      <ClockIcon className="h-[9px] w-[9px]" />
      {overdue ? "Vencido" : "Seguimiento"}
    </span>
  );
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}
