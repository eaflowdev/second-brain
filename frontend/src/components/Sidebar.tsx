import { useEffect, useState } from "react";
import { scanNotes, type NoteDocument } from "../lib/api";
import { UploadNotes } from "./UploadNotes";

export function Sidebar() {
  const [documents, setDocuments] = useState<NoteDocument[]>([]);

  async function refresh() {
    try {
      const result = await scanNotes();
      setDocuments(result.documents);
    } catch {
      // le backend n'est peut-être pas encore lancé — on réessaiera au prochain refresh
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 border-r border-slate-800 bg-slate-950 p-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-white">
          <span aria-hidden>🧠</span> Second Brain
        </h1>
        <p className="mt-1 text-xs text-slate-500">Agent de révision personnel</p>
      </div>

      <UploadNotes onIndexed={refresh} />

      <div className="flex-1 overflow-y-auto">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          Notes indexées ({documents.length})
        </p>
        <ul className="flex flex-col gap-1.5">
          {documents.map((doc) => (
            <li
              key={doc.id}
              className="truncate rounded-lg bg-slate-900/60 px-3 py-2 text-xs text-slate-300"
              title={doc.title}
            >
              <span className="mr-1.5">{doc.doc_type === "pdf" ? "📄" : "📝"}</span>
              {doc.title}
            </li>
          ))}
          {documents.length === 0 && (
            <li className="rounded-lg px-3 py-2 text-xs text-slate-600">Aucune note pour l'instant.</li>
          )}
        </ul>
      </div>
    </aside>
  );
}
