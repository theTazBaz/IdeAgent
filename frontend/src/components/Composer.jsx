import { useRef, useState } from "react";

export default function Composer({ onSend, disabled }) {
  const [text, setText] = useState("");
  const ref = useRef(null);

  function submit(e) {
    e?.preventDefault();
    const q = text.trim();
    if (q.length < 3 || disabled) return;
    onSend(q);
    setText("");
    if (ref.current) ref.current.style.height = "auto";
  }

  function resize(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  return (
    <form onSubmit={submit} className="border-t border-stone-200 px-4 py-3 dark:border-stone-800">
      <div className="mx-auto flex max-w-3xl gap-2">
        <textarea
          ref={ref}
          rows={1}
          maxLength={500}
          value={text}
          placeholder="e.g. A song that captures the emotional intensity of Interstellar"
          onChange={(e) => {
            setText(e.target.value);
            resize(e.target);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) submit(e);
          }}
          className="flex-1 resize-none rounded-xl border border-stone-200 bg-white px-4 py-2.5 outline-none focus:ring-2 focus:ring-indigo-500 dark:border-stone-800 dark:bg-stone-900"
        />
        <button
          type="submit"
          disabled={disabled || text.trim().length < 3}
          className="rounded-xl bg-indigo-600 px-5 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Ask
        </button>
      </div>
    </form>
  );
}
