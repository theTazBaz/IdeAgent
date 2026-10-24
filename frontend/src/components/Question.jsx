export default function Question({ text }) {
  return (
    <div className="mb-3 mt-6 flex justify-end">
      <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2 text-white">{text}</div>
    </div>
  );
}
