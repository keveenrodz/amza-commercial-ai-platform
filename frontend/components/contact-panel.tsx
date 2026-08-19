"use client";

import { useState } from "react";

import { DateTimePicker } from "@/components/date-time-picker";
import { ClockIcon, CloseIcon, StarIcon } from "@/components/icons";
import { initials } from "@/components/status-chips";
import { useAddContactNote, useContactNotes } from "@/hooks/use-contact-notes";
import { useAddContactTag, useRemoveContactTag } from "@/hooks/use-contact-tags";
import { useResolveFollowUp, useScheduleFollowUp } from "@/hooks/use-follow-up";
import { useToggleFavorite } from "@/hooks/use-toggle-favorite";
import type { ContactSummary, FollowUp } from "@/types/api";

export function ContactPanel({
  organizationSlug,
  opportunityId,
  contactId,
  contact,
  followUp,
  advisorId,
  onClose,
}: {
  organizationSlug: string;
  opportunityId: string;
  contactId: string;
  contact: ContactSummary;
  followUp: FollowUp | null;
  advisorId: string;
  onClose: () => void;
}) {
  const [addingTag, setAddingTag] = useState(false);
  const [tagDraft, setTagDraft] = useState("");
  const [noteDraft, setNoteDraft] = useState("");
  const [schedulingFollowUp, setSchedulingFollowUp] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dueAt, setDueAt] = useState<Date | null>(null);
  const [followUpReason, setFollowUpReason] = useState("");

  const toggleFavorite = useToggleFavorite();
  const addTag = useAddContactTag();
  const removeTag = useRemoveContactTag();
  const { data: notes, isLoading: notesLoading } = useContactNotes(organizationSlug, contactId);
  const addNote = useAddContactNote();
  const scheduleFollowUp = useScheduleFollowUp();
  const resolveFollowUp = useResolveFollowUp();

  const isOverdue = followUp ? new Date(followUp.due_at) < new Date() : false;

  return (
    <aside className="flex h-full w-[300px] flex-shrink-0 flex-col overflow-y-auto border-l border-line bg-surface p-4">
      <div className="mb-1 flex justify-end">
        <button
          onClick={onClose}
          aria-label="Cerrar"
          className="flex h-8 w-8 items-center justify-center rounded-full text-ink-muted hover:bg-surface-2"
        >
          <CloseIcon className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-3.5 flex flex-col items-center border-b border-line pb-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-3 font-heading text-sm font-bold text-ink-muted">
          {initials(contact.display_name)}
        </div>
        <div className="mt-2.5 flex items-center gap-1.5">
          <h3 className="font-heading text-[15px] font-bold text-ink">{contact.display_name}</h3>
          <button
            onClick={() =>
              toggleFavorite.mutate({ organizationSlug, opportunityId, contactId })
            }
            aria-label="Marcar como preferido"
            className={contact.is_favorite ? "text-gold" : "text-ink-faint"}
          >
            <StarIcon filled={contact.is_favorite} className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="mb-2 font-heading text-[11px] uppercase tracking-wide text-ink-faint">
          Información
        </h4>
        <div className="flex justify-between text-[12.5px]">
          <span className="text-ink-muted">Teléfono</span>
          <span className="font-semibold text-ink">{contact.phone_number ?? "—"}</span>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="mb-2 font-heading text-[11px] uppercase tracking-wide text-ink-faint">
          Etiquetas
        </h4>
        <div className="flex flex-wrap items-center gap-1.5">
          {contact.tags.map((tag) => (
            <span
              key={tag}
              className="flex items-center gap-1 rounded-full bg-accent-soft px-2.5 py-1 text-[11.5px] font-semibold text-accent-deep"
            >
              {tag}
              <button
                onClick={() =>
                  removeTag.mutate({ organizationSlug, opportunityId, contactId, tag })
                }
                aria-label={`Quitar etiqueta ${tag}`}
                className="text-accent-deep/70 hover:text-accent-deep"
              >
                <CloseIcon className="h-2.5 w-2.5" />
              </button>
            </span>
          ))}
          {addingTag ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!tagDraft.trim()) return;
                addTag.mutate(
                  { organizationSlug, opportunityId, contactId, tag: tagDraft.trim() },
                  { onSuccess: () => setTagDraft("") },
                );
                setAddingTag(false);
              }}
              className="flex gap-1"
            >
              <input
                autoFocus
                value={tagDraft}
                onChange={(e) => setTagDraft(e.target.value)}
                onBlur={() => setAddingTag(false)}
                placeholder="Nueva etiqueta"
                className="w-28 rounded-lg border border-line bg-paper px-2 py-1 text-[11px] text-ink"
              />
            </form>
          ) : (
            <button
              onClick={() => setAddingTag(true)}
              className="rounded-full border border-dashed border-line px-2.5 py-1 text-[11px] font-bold text-ink-muted"
            >
              + Etiqueta
            </button>
          )}
        </div>
      </div>

      <div className="mb-4">
        <h4 className="mb-2 font-heading text-[11px] uppercase tracking-wide text-ink-faint">
          Seguimiento
        </h4>
        {followUp ? (
          <div
            className={`rounded-[10px] p-2.5 text-xs ${
              isOverdue ? "bg-overdue-soft" : "bg-warn-soft"
            }`}
          >
            <p
              className={`mb-1 flex items-center gap-1.5 font-bold ${
                isOverdue ? "text-overdue" : "text-warn"
              }`}
            >
              <ClockIcon className="h-3.5 w-3.5" />
              {new Date(followUp.due_at).toLocaleString("es-CO", {
                day: "numeric",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            <p className="mb-2 text-ink-muted">{followUp.reason}</p>
            <button
              onClick={() => resolveFollowUp.mutate({ organizationSlug, opportunityId })}
              disabled={resolveFollowUp.isPending}
              className="w-full rounded-[7px] border border-line bg-surface px-2 py-1 text-[11.5px] font-bold text-ink"
            >
              Marcar como resuelto
            </button>
          </div>
        ) : schedulingFollowUp ? (
          <div className="flex flex-col gap-1.5">
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowDatePicker((v) => !v)}
                className="w-full rounded-[7px] border border-line bg-paper px-2 py-1.5 text-left text-xs text-ink-muted"
              >
                {dueAt
                  ? dueAt.toLocaleString("es-CO", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Elige fecha y hora"}
              </button>
              {showDatePicker && (
                <DateTimePicker
                  onSelect={(date) => {
                    setDueAt(date);
                    setShowDatePicker(false);
                  }}
                  onClose={() => setShowDatePicker(false)}
                />
              )}
            </div>
            <input
              value={followUpReason}
              onChange={(e) => setFollowUpReason(e.target.value)}
              placeholder="Motivo del seguimiento"
              className="rounded-[7px] border border-line bg-paper px-2 py-1.5 text-xs text-ink"
            />
            <button
              onClick={() => {
                if (!dueAt) return;
                scheduleFollowUp.mutate(
                  {
                    organizationSlug,
                    opportunityId,
                    advisorId,
                    dueAt: dueAt.toISOString(),
                    reason: followUpReason,
                  },
                  {
                    onSuccess: () => {
                      setSchedulingFollowUp(false);
                      setDueAt(null);
                      setFollowUpReason("");
                    },
                  },
                );
              }}
              disabled={!dueAt || scheduleFollowUp.isPending}
              className="rounded-[7px] bg-accent px-2 py-1.5 text-[11.5px] font-bold text-white disabled:opacity-50"
            >
              Guardar seguimiento
            </button>
          </div>
        ) : (
          <button
            onClick={() => setSchedulingFollowUp(true)}
            className="w-full rounded-[7px] border border-dashed border-line px-2 py-1.5 text-center text-xs text-ink-muted"
          >
            + Programar seguimiento
          </button>
        )}
      </div>

      <div>
        <h4 className="mb-2 font-heading text-[11px] uppercase tracking-wide text-ink-faint">
          Notas
        </h4>
        <div className="mb-2 flex flex-col gap-2">
          {notesLoading ? (
            <p className="text-xs text-ink-faint">Cargando notas...</p>
          ) : notes && notes.length > 0 ? (
            notes.map((note) => (
              <div key={note.id} className="rounded-[9px] bg-surface-2 p-2 text-xs">
                <div className="mb-1 flex justify-between font-heading font-bold text-ink-muted">
                  <span>{note.author_name}</span>
                  <span>
                    {new Date(note.created_at).toLocaleDateString("es-CO", {
                      day: "numeric",
                      month: "short",
                    })}
                  </span>
                </div>
                <p className="text-ink">{note.content}</p>
              </div>
            ))
          ) : (
            <p className="text-xs text-ink-faint">Sin notas todavía.</p>
          )}
        </div>
        <textarea
          value={noteDraft}
          onChange={(e) => setNoteDraft(e.target.value)}
          placeholder="Agregar una nota sobre este cliente..."
          rows={2}
          className="mb-1.5 w-full resize-none rounded-lg border border-line bg-paper px-2 py-1.5 text-xs text-ink"
        />
        <button
          onClick={() =>
            addNote.mutate(
              { organizationSlug, contactId, advisorId, content: noteDraft },
              { onSuccess: () => setNoteDraft("") },
            )
          }
          disabled={!noteDraft.trim() || addNote.isPending}
          className="w-full rounded-lg bg-accent px-2 py-1.5 text-xs font-bold text-white hover:bg-accent-deep disabled:opacity-50"
        >
          Guardar nota
        </button>
      </div>
    </aside>
  );
}
