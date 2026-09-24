import { useState } from "react";

export function ThinkingPanel({ plan, thinking }: { plan?: string; thinking: string[] }) {
  const [open, setOpen] = useState(false);
  if (!plan && thinking.length === 0) return null;

  return (
    <div className="rounded-lg border border-indigo-900/50 bg-indigo-950/30">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-indigo-300 hover:text-indigo-200"
      >
        <span>🧠 Raisonnement de l'agent</span>
        <span className="text-indigo-500">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="space-y-3 border-t border-indigo-900/50 px-3 py-2 text-xs text-indigo-200/80">
          {plan && (
            <div>
              <p className="mb-1 font-semibold text-indigo-300">Plan envisagé</p>
              <p className="whitespace-pre-wrap">{plan}</p>
            </div>
          )}
          {thinking.map((thought, index) => (
            <div key={index}>
              <p className="mb-1 font-semibold text-indigo-300">
                Réflexion {thinking.length > 1 ? `#${index + 1}` : ""}
              </p>
              <p className="whitespace-pre-wrap">{thought}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
