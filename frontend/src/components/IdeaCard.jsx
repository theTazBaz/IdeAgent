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
      </div>

      {idea.why && <p className="mt-2 text-[0.95rem] text-stone-600 dark:text-stone-400">{idea.why}</p>}

      {idea.idea && (
        <p className="mt-2 rounded-lg bg-indigo-50 px-3 py-2 text-[0.95rem] dark:bg-indigo-950">
          <b className="text-indigo-700 dark:text-indigo-300">Idea:</b> {idea.idea}
        </p>
      )}

      {loose ? (
        <p className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-400">loosely related</p>
      ) : (
        <p className="mt-2 text-xs tabular-nums text-stone-500">match strength {(idea.similarity * 100).toFixed(0)}%</p>
      )}
    </article>
  );
}
