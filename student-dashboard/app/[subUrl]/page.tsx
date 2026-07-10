import { fetchStudentPage } from "@/lib/api";
import { StudentPageData } from "@/lib/types";
import HeaderCard from "@/components/HeaderCard";
import DailyPulseCard from "@/components/DailyPulseCard";
import TafsirCard from "@/components/TafsirCard";
import WeeklyCard from "@/components/WeeklyCard";

import BigPictureCard from "@/components/BigPictureCard";
import ShareCard from "@/components/ShareCard";

interface PageProps {
  params: Promise<{ subUrl: string }>;
}

export default async function StudentPage({ params }: PageProps) {
  const { subUrl } = await params;

  let data: StudentPageData;
  let errorMsg = "";
  try {
    data = await fetchStudentPage(subUrl);
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    console.error("StudentPage fetch error:", errorMsg);
    return (
      <div className="error-screen">
        <div style={{ fontSize: 48 }}>📖</div>
        <div
          style={{
            fontFamily: "var(--font-amiri), Amiri, serif",
            fontSize: 22,
            fontWeight: 700,
          }}
        >
          لم يتم العثور على الطالب
        </div>
        <div style={{ fontSize: 14, color: "var(--text-muted)" }}>
          تأكد من صحة الرابط وحاول مرة أخرى
        </div>
        <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 8, direction: "ltr" as const }}>
          {errorMsg}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <HeaderCard data={data} />
      <DailyPulseCard data={data} />
      <TafsirCard data={data} />
      <WeeklyCard data={data} />

      <BigPictureCard data={data} />
      <ShareCard data={data} />
    </div>
  );
}
