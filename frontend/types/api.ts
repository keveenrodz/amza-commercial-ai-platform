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
  is_primary: boolean;
}

export interface InternalUserSummary {
  id: string;
  full_name: string;
  email: string;
  role: "advisor" | "administrator";
  status: "active" | "inactive";
  is_primary: boolean;
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
  unread_count: number;
}

export interface ContactSummary {
  display_name: string;
  phone_number: string | null;
  tags: string[];
  is_favorite: boolean;
}

export interface FollowUp {
  id: string;
  due_at: string;
  reason: string;
}

export interface OpenOpportunity {
  opportunity: Opportunity;
  contact: ContactSummary;
  follow_up: FollowUp | null;
  last_message_preview: string | null;
}

export interface Message {
  id: string;
  sender_role: "user" | "assistant" | "advisor" | "system";
  content: string;
  content_type: string;
  sent_at: string;
}

export interface ConversationHistory {
  opportunity: Opportunity;
  contact: ContactSummary;
  follow_up: FollowUp | null;
  messages: Message[];
}

export interface AdvisorSummary {
  id: string;
  full_name: string;
}

export interface ContactNote {
  id: string;
  author_name: string;
  content: string;
  created_at: string;
}

export interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  escalation_rules: string;
  model: string;
}

export interface WhatsAppStatus {
  connected: boolean;
  phone_number: string | null;
}
