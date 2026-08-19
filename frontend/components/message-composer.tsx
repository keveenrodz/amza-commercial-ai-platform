"use client";

import { useRef, useState } from "react";

import { EmojiPicker } from "@/components/emoji-picker";
import { EmojiIcon, SendIcon } from "@/components/icons";

export function MessageComposer({
  value,
  onChange,
  onSubmit,
  isSending,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isSending: boolean;
  placeholder: string;
}) {
  const [showEmoji, setShowEmoji] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function insertEmoji(emoji: string) {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? value.length;
    onChange(value.slice(0, start) + emoji + value.slice(end));
    requestAnimationFrame(() => {
      el?.focus();
      if (el) el.selectionStart = el.selectionEnd = start + emoji.length;
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim()) return;
    onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="relative flex items-end gap-2">
      <button
        type="button"
        onClick={() => setShowEmoji((v) => !v)}
        aria-label="Insertar emoticón"
        className="flex h-[38px] w-[38px] flex-shrink-0 items-center justify-center rounded-full text-ink-muted hover:bg-surface-2"
      >
        <EmojiIcon className="h-5 w-5" />
      </button>
      {showEmoji && <EmojiPicker onPick={insertEmoji} onClose={() => setShowEmoji(false)} />}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
        placeholder={placeholder}
        rows={1}
        disabled={isSending}
        className="max-h-32 flex-1 resize-none rounded-xl border border-line bg-paper px-3.5 py-2.5 text-[13.5px] text-ink placeholder:text-ink-faint focus:border-accent focus:outline-none"
      />
      <button
        type="submit"
        aria-label="Enviar"
        disabled={isSending || !value.trim()}
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-accent text-white hover:bg-accent-deep disabled:opacity-50"
      >
        <SendIcon className="h-[17px] w-[17px]" />
      </button>
    </form>
  );
}
