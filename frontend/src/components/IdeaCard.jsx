// full class names so Tailwind can see them
const TYPE_STYLE = {
  movie: "text-orange-700 dark:text-orange-400",
  character: "text-teal-700 dark:text-teal-400",
  relationship: "text-fuchsia-700 dark:text-fuchsia-400",
  song: "text-blue-700 dark:text-blue-400",
};

export default function IdeaCard({ idea, loose = false }) {
  return (
    <article
      className={`mb-2.5 rounded-xl border bg-white p-4 dark:bg-stone-900 ${
        loose ? "border-dashed border-amber-300 dark:border-amber-800" : "border-stone-200 dark:border-stone-800"
      }`}
    >
      <div className="flex items-center gap-2.5">
        <span className="grid size-7 flex-none place-items-center rounded-full bg-indigo-50 text-sm font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
          {idea.rank}
        </span>
        <h3 className="min-w-0 flex-1 break-words font-semibold">{idea.name}</h3>
        <span className={`text-[0.7rem] font-bold uppercase tracking-wider ${TYPE_STYLE[idea.type] ?? "text-stone-500"}`}>
          {idea.type}
        </span>
        {idea.trend?.in_chart && (
          <span
            className="rounded-full bg-emerald-50 px-2 py-0.5 text-[0.7rem] font-semibold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
            title={`In Last.fm's current global top 1000 (#${idea.trend.rank})`}
          >
            trending
          </span>
        )}
      </div>

      {idea.why && <p className="mt-2 text-[0.95rem] text-stone-600 dark:text-stone-400">{idea.why}</p>}

      {idea.idea && (
        <p className="mt-2 rounded-lg bg-indigo-50 px-3 py-2 text-[0.95rem] dark:bg-indigo-950">
          <b className="text-indigo-700 dark:text-indigo-300">Idea:</b> {idea.idea}
        </p>
      )}

      {loose ? (
        <p className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-400">loosely related</p>
      ) : idea.r_score != null ? (
        <div
          className="mt-3 flex items-center gap-2 text-xs tabular-nums text-stone-500"
          title={
            idea.dims
              ? `emotional match ${idea.dims.emotional_match} · tone ${idea.dims.tone} · usability ${idea.dims.usability}`
              : undefined
          }
        >
          <span className="font-medium">fit {Math.round(idea.r_score * 100)}%</span>
          <span className="h-1.5 w-20 overflow-hidden rounded-full bg-stone-200 dark:bg-stone-800">
            <span className="block h-full bg-indigo-500" style={{ width: `${Math.round(idea.r_score * 100)}%` }} />
          </span>
          <span>similarity {idea.similarity.toFixed(2)}</span>
        </div>
      ) : (
        <p className="mt-2 text-xs tabular-nums text-stone-500">match strength {(idea.similarity * 100).toFixed(0)}%</p>
      )}
    </article>
  );
}
