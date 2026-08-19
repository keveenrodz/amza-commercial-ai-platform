import { FileIcon } from "@/components/icons";

// Sin visor real todavía -- solo una representación honesta de que ahí hay un adjunto
// (descargar/almacenar multimedia es Media Library, más adelante en la tanda).
const LABELS: Record<string, string> = {
  image: "Imagen",
  video: "Video",
  document: "Documento",
  audio: "Audio",
  location: "Ubicación",
};

export function FileCard({ type }: { type: string }) {
  return (
    <div className="flex items-center gap-2 rounded-[9px] bg-black/5 px-2.5 py-2 dark:bg-white/[0.06]">
      <div className="flex h-[30px] w-[30px] flex-shrink-0 items-center justify-center rounded-[7px] bg-accent-soft text-accent-deep">
        <FileIcon className="h-[15px] w-[15px]" />
      </div>
      <span className="text-[12.5px] font-semibold text-ink">{LABELS[type] ?? type}</span>
    </div>
  );
}
