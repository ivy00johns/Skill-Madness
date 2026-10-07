export function Button({ label }: { label: string }) {
  return (
    <button
      className="flex items-center justify-between gap-4 rounded-md"
      style={{ backgroundColor: "#1d4ed8", color: "#ffffff" }}
    >
      {label}
    </button>
  );
}
