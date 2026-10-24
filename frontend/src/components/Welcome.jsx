const EXAMPLES = [
  "A song that captures the emotional intensity of Interstellar",
  "Movies that feel like La La Land",
  "Characters with a moral conflict like The Joker",
  "A song for a bittersweet goodbye scene",
];

export default function Welcome({ onPick, disabled }) {
  return (
    <div className="mt-[8vh] text-center">
      <h2 className="text-3xl font-semibold">What are you making?</h2>
      <p className="mb-6 mt-2 text-stone-500">
        Ask for a song, movie or character that matches the feeling you want.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((e) => (
          <button
            key={e}
            type="button"
            disabled={disabled}
            onClick={() => onPick(e)}
            className="rounded-full border border-stone-200 bg-white px-3.5 py-2 text-sm text-stone-600 transition hover:border-indigo-500 hover:text-stone-900 disabled:opacity-50 dark:border-stone-800 dark:bg-stone-900 dark:text-stone-400 dark:hover:text-stone-100"
          >
            {e}
          </button>
        ))}
      </div>
    </div>
  );
}
