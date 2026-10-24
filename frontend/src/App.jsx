import { useEffect, useRef, useState } from "react";
import { search } from "./api.js";
import Welcome from "./components/Welcome.jsx";
import Question from "./components/Question.jsx";
import Answer from "./components/Answer.jsx";
import Composer from "./components/Composer.jsx";

export default function App() {
  // each turn: { id, query, status: "loading" | "done" | "error", data?, error? }
  const [turns, setTurns] = useState([]);
  const busy = turns.some((t) => t.status === "loading");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  async function ask(query) {
    const id = crypto.randomUUID();
    setTurns((t) => [...t, { id, query, status: "loading" }]);
    try {
      const data = await search(query);
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, status: "done", data } : x)));
    } catch (err) {
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, status: "error", error: err.message } : x)));
    }
  }

  return (
    <div className="flex h-dvh flex-col bg-stone-50 text-stone-900 dark:bg-stone-950 dark:text-stone-100">
      <header className="flex items-baseline gap-3 border-b border-stone-200 px-4 py-3 dark:border-stone-800">
        <h1 className="text-lg font-semibold">IdeAgent</h1>
        <span className="hidden text-sm text-stone-500 sm:inline">
          Content ideas grounded in movies, characters and music
        </span>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-5">
        <div className="mx-auto max-w-3xl">
          {turns.length === 0 ? (
            <Welcome onPick={ask} disabled={busy} />
          ) : (
            turns.map((t) => (
              <div key={t.id}>
                <Question text={t.query} />
                <Answer turn={t} />
              </div>
            ))
          )}
          <div ref={endRef} />
        </div>
      </main>

      <Composer onSend={ask} disabled={busy} />
    </div>
  );
}
