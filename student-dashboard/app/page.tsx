export default function Home() {
  return (
    <div className="loading-screen">
      <div style={{ fontSize: 48 }}>📖</div>
      <div
        style={{
          fontFamily: "var(--font-amiri), Amiri, serif",
          fontSize: 24,
          fontWeight: 700,
          color: "var(--gold)",
        }}
      >
        شامل
      </div>
      <div style={{ fontSize: 14, color: "var(--text-muted)", textAlign: "center" }}>
        منصة بيانات الطالب الشامل
        <br />
        أدخل الرابط الخاص بالطالب
      </div>
    </div>
  );
}
