// Espejo de los DTOs de backend/app/api/dto/*.py -- mantener sincronizado a mano, no hay
// generación de tipos compartidos todavía (no hace falta a este tamaño de proyecto).

export interface CurrentUser {
  id: string;
  organization_id: string;
  organization_slug: string;
  full_name: string;
  email: string;
  role: "advisor" | "administrator";
  status: "active" | "inactive";
}

export interface Opportunity {
  id: string;
  contact_id: string;
  agent_id: string;
  assigned_advisor_id: string | null;
  attention_mode: "ai" | "human";
  status: string;
  channel_type: string;
  started_at: string;
  last_activity_at: string;
  closed_at: string | null;
}

export interface Message {
  id: string;
  sender_role: "user" | "assistant" | "system";
  content: string;
  content_type: string;
  sent_at: string;
}

export interface ConversationHistory {
  opportunity: Opportunity;
  messages: Message[];
}
