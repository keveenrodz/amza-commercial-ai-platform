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
    <div className="flex items-center gap-2 rounded-lg bg-black/5 px-2.5 py-2 dark:bg-white/10">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
        <FileIcon className="h-4 w-4" />
      </div>
      <span className="text-sm font-medium">{LABELS[type] ?? type}</span>
    </div>
  );
}
