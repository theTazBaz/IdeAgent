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

      {intent.reference_entity && !d.reference && (
        <p className="mb-3 rounded-lg border border-dashed border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-500 dark:border-stone-700 dark:bg-stone-900">
          “{intent.reference_entity}” isn’t in the database, so your question was matched as written.
        </p>
      )}

      {d.results.length === 0 ? (
        <p className="text-lg">
          Nothing in the database matched that. Try rephrasing, or ask about a different movie, character or song.
        </p>
      ) : (
        <>
          {d.summary && <p className="mb-3 text-lg">{d.summary}</p>}
          {d.ideas.map((idea) => (
            <IdeaCard key={idea.rank} idea={idea} />
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
