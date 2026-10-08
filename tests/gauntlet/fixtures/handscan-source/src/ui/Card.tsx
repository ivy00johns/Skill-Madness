export function Card({ title }: { title: string }) {
  return (
    <section
      className="flex items-center justify-between gap-4 rounded-md"
      style={{ borderColor: "rgb(229, 231, 235)" }}
    >
      <h2 style={{ color: "hsl(0, 0%, 0%)" }}>{title}</h2>
    </section>
  );
}
