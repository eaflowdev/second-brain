import { useRef, useState } from "react";
import { reindexNotes, uploadNote } from "../lib/api";

export function UploadNotes({ onIndexed }: { onIndexed: (count: number) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "indexing" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setStatus("uploading");
    setMessage("");

    try {
      for (const file of Array.from(files)) {
        await uploadNote(file);
      }
      setStatus("indexing");
      const result = await reindexNotes();
      setStatus("done");
      setMessage(`${result.chunks_indexed} chunk(s) indexé(s) sur ${result.documents_indexed} note(s).`);
      onIndexed(result.documents_indexed);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Erreur inconnue");
    }
  }

  const busy = status === "uploading" || status === "indexing";

  return (
    <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-4">
      <input
        ref={inputRef}
        type="file"
        accept=".md,.markdown,.pdf"
        multiple
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
      >
        {status === "uploading" && "Envoi en cours..."}
        {status === "indexing" && "Indexation en cours..."}
        {(status === "idle" || status === "done" || status === "error") && "📎 Ajouter des notes (.md, .pdf)"}
      </button>
      {message && (
        <p className={`mt-2 text-xs ${status === "error" ? "text-red-400" : "text-emerald-400"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
