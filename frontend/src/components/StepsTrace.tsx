interface ToolStep {
  tool: string;
  input: Record<string, unknown>;
  output?: string;
}

const TOOL_LABELS: Record<string, string> = {
  search_notes: "Recherche dans les notes",
  search_web: "Recherche web",
  load_skill: "Chargement d'une compétence",
};

export function StepsTrace({ steps }: { steps: ToolStep[] }) {
  if (steps.length === 0) return null;

  return (
    <ol className="flex flex-col gap-2">
      {steps.map((step, index) => (
        <li
          key={`${step.tool}-${index}`}
          className="rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm"
        >
          <div className="flex items-center gap-2">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                step.output !== undefined ? "bg-emerald-400" : "animate-pulse bg-amber-400"
              }`}
            />
            <span className="font-medium text-slate-200">
              {TOOL_LABELS[step.tool] ?? step.tool}
            </span>
            <code className="truncate text-xs text-slate-500">
              {JSON.stringify(step.input)}
            </code>
          </div>
          {step.output !== undefined && (
            <p className="mt-1.5 line-clamp-3 text-xs text-slate-400">{step.output}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
