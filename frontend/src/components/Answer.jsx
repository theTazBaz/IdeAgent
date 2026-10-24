import IdeaCard from "./IdeaCard.jsx";

function Tag({ label, value }) {
  if (!value) return null;
  return (
    <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
      {label}: {value}
    </span>
  );
}

function Dots() {
  return (
    <span aria-hidden>
      {[0, 1, 2].map((i) => (
        <span key={i} className="inline-block" style={{ animation: "dot 1.2s infinite", animationDelay: `${i * 0.2}s` }}>
          .
        </span>
      ))}
    </span>
  );
}

export default function Answer({ turn }) {
  if (turn.status === "loading") {
    return (
      <p className="text-stone-500" role="status">
        Searching the knowledge base <Dots />
      </p>
    );
  }
  if (turn.status === "error") {
    return (
      <p className="rounded-lg border border-red-500 bg-white px-4 py-2.5 text-red-600 dark:bg-stone-900 dark:text-red-400" role="alert">
        {turn.error}
      </p>
    );
  }

  const d = turn.data;
  const intent = d.intent || {};

  return (
    <section className="mb-2">
      <div className="mb-3 flex flex-wrap gap-1.5">
        <Tag label="About" value={intent.reference_entity} />
        <Tag label="Looking for" value={intent.target_type} />
        <Tag label="Matching" value={intent.matching_concept} />
      </div>

      {d.confidence === "low" && d.confidence_reason && (
        <div
          role="note"
          className="mb-3 flex gap-2.5 rounded-lg border border-amber-300 bg-amber-50 px-3.5 py-2.5 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
        >
          <span aria-hidden>⚠️</span>
          <p>
            <b>Limited confidence.</b> {d.confidence_reason}
          </p>
        </div>
      )}

      {d.reference_source === "live" && d.confidence !== "low" && d.confidence_reason && (
        <p
          role="note"
          className="mb-3 rounded-lg border border-sky-300 bg-sky-50 px-3.5 py-2.5 text-sm text-sky-900 dark:border-sky-800 dark:bg-sky-950 dark:text-sky-200"
        >
          <b>Looked up live.</b> {d.confidence_reason}
        </p>
      )}

      {d.results.length === 0 ? (
        <p className="text-lg">
          Nothing in the database matched that. Try rephrasing, or ask about a different movie, character or song.
        </p>
      ) : (
        <>
          {d.summary && <p className="mb-3 text-lg">{d.summary}</p>}
          {d.confidence === "low" && d.ideas.length === 0 && (
            <p className="mb-3 text-stone-500">None of the entries we have fit this request.</p>
          )}
          {d.ideas.map((idea) => (
            <IdeaCard key={idea.rank} idea={idea} loose={d.confidence === "low"} />
          ))}
          <details className="mt-2 text-sm text-stone-500">
            <summary className="cursor-pointer">How this was found</summary>
            <p className="mt-2">
              <b>Search text:</b> {d.search_string}
            </p>
            <p className="mt-1">
              <b>Closest matches by similarity:</b>{" "}
              {d.results.map((r) => `${r.name} (${r.similarity.toFixed(3)})`).join(" · ")}
            </p>
          </details>
        </>
      )}
    </section>
  );
}
