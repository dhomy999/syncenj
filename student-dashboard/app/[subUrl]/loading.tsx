export default function Loading() {
  return (
    <div className="loading-screen">
      <div className="loading-spinner" />
      <div
        style={{
          fontFamily: "var(--font-amiri), Amiri, serif",
          fontSize: 20,
          fontWeight: 700,
          color: "var(--gold)",
        }}
      >
        شامل
      </div>
      <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
        جارٍ تحميل البيانات...
      </div>
    </div>
  );
}
