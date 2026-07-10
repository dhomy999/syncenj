import Badge from "./ui/Badge";
import { StudentPageData } from "@/lib/types";

interface DailyPulseCardProps {
  data: StudentPageData;
}

interface LessonFrom { surah_name: string; verse_order: number; page_no: number }
interface LessonTo { surah_name: string; verse_order: number; page_no: number }
interface Lesson { pillar_id: number; from: LessonFrom; to: LessonTo; done: boolean }
interface Level { lessons: Lesson[] }
interface TodayData { levels?: Level[]; rating?: number; grade?: string | null; attend_type?: string }

function formatLesson(lesson: Lesson): string {
  const from = lesson.from;
  const to = lesson.to;
  if (from.surah_name === to.surah_name) {
    return `${from.surah_name} (${from.verse_order}-${to.verse_order})`;
  }
  return `${from.surah_name} ${from.verse_order} - ${to.surah_name} ${to.verse_order}`;
}

function extractLessons(todayLessons: Record<string, unknown>): { saved: string; revised: string; grade: string | null; attendType: string } {
  const data = todayLessons as TodayData;
  let saved = "—";
  let revised = "—";

  const allLessons = data.levels?.flatMap(l => l.lessons) || [];

  // pillar_id: 2 = حفظ, 3 = مراجعة كبرى, 4 = مراجعة صغرى
  const savedLesson = allLessons.find(l => l.pillar_id === 2);
  const revisedLesson = allLessons.find(l => l.pillar_id === 3 || l.pillar_id === 4);

  if (savedLesson) saved = formatLesson(savedLesson);
  if (revisedLesson) revised = formatLesson(revisedLesson);

  return {
    saved,
    revised,
    grade: data.grade || null,
    attendType: data.attend_type || "",
  };
}

export default function DailyPulseCard({ data }: DailyPulseCardProps) {
  const { report, today_lessons } = data;
  if (!report?.saved_pages && !report?.revision_pages && !today_lessons) return null;

  let lastSaved: string;
  let lastRevised: string;
  let grade: string;

  if (today_lessons && Object.keys(today_lessons).length > 0) {
    // Use today_lessons exclusively
    const extracted = extractLessons(today_lessons);
    lastSaved = extracted.saved === "—" ? "لا يوجد درس اليوم" : extracted.saved;
    lastRevised = extracted.revised === "—" ? "لا توجد مراجعة اليوم" : extracted.revised;
    grade = extracted.grade || report?.rating?.grade || "—";
  } else {
    // Fallback to report data
    lastSaved = report?.saved_pages?.history_lessons?.[0]?.text || "لا يوجد درس اليوم";
    lastRevised = report?.revision_pages?.history_lessons?.[0]?.text || "لا توجد مراجعة اليوم";
    grade = report?.rating?.grade || "—";
  }

  return (
    <div className="card">
      <div className="card-label">نبضة اليوم</div>
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        {/* Last memorized */}
        <div
          style={{
            flex: 1,
            background: "oklch(0.52 0.11 162 / 0.06)",
            border: "1px solid oklch(0.52 0.11 162 / 0.18)",
            borderRadius: 12,
            padding: "13px 14px",
          }}
        >
          <div
            style={{
              fontSize: 10,
              color: "var(--jade)",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase" as const,
              marginBottom: 7,
            }}
          >
            درس اليوم
          </div>
          <div
            style={{
              fontFamily: "var(--font-amiri), Amiri, serif",
              fontSize: 15,
              fontWeight: 700,
              lineHeight: 1.6,
            }}
          >
            {lastSaved}
          </div>
        </div>

        {/* Last reviewed */}
        <div
          style={{
            flex: 1,
            background: "oklch(0.62 0.14 55 / 0.06)",
            border: "1px solid oklch(0.62 0.14 55 / 0.18)",
            borderRadius: 12,
            padding: "13px 14px",
          }}
        >
          <div
            style={{
              fontSize: 10,
              color: "var(--amber)",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase" as const,
              marginBottom: 7,
            }}
          >
            مراجعة اليوم
          </div>
          <div
            style={{
              fontFamily: "var(--font-amiri), Amiri, serif",
              fontSize: 15,
              fontWeight: 700,
              lineHeight: 1.6,
            }}
          >
            {lastRevised}
          </div>
        </div>
      </div>

    </div>
  );
}
