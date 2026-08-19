import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EmojiPicker } from "@/components/emoji-picker";

// Cubre spec 012, sección 6: el selector de emojis muestra 👍/✅/🙏 por defecto antes de
// cualquier uso, y promueve un emoji a "Frecuentes" tras usarlo.

describe("EmojiPicker", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("muestra los tres emojis por defecto antes de cualquier uso", () => {
    render(<EmojiPicker onPick={() => {}} onClose={() => {}} />);

    const frequentSection = screen.getByText("Frecuentes").closest("div")!;
    expect(within(frequentSection).getByText("👍")).toBeInTheDocument();
    expect(within(frequentSection).getByText("✅")).toBeInTheDocument();
    expect(within(frequentSection).getByText("🙏")).toBeInTheDocument();
  });

  it("promueve un emoji a Frecuentes después de usarlo", () => {
    const onPick = vi.fn();
    render(<EmojiPicker onPick={onPick} onClose={() => {}} />);

    fireEvent.click(screen.getByText("🔥"));
    expect(onPick).toHaveBeenCalledWith("🔥");

    const frequentSection = screen.getByText("Frecuentes").closest("div")!;
    expect(within(frequentSection).getByText("🔥")).toBeInTheDocument();
  });

  it("filtra por palabra clave al escribir en el buscador", () => {
    render(<EmojiPicker onPick={() => {}} onClose={() => {}} />);

    fireEvent.change(screen.getByPlaceholderText("Buscar emoji"), {
      target: { value: "factura" },
    });

    expect(screen.getByText("🧾")).toBeInTheDocument();
    expect(screen.queryByText("😀")).not.toBeInTheDocument();
  });
});
