import Image from "next/image";
import { StudentPageData } from "@/lib/types";

interface HeaderCardProps {
  data: StudentPageData;
}

function InfoRow({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
      <span
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: "var(--text-dim)",
          minWidth: 50,
          flexShrink: 0,
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: bold ? 16 : 14,
          fontWeight: bold ? 700 : 500,
          color: "var(--text)",
          lineHeight: 1.6,
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function HeaderCard({ data }: HeaderCardProps) {
  const { personal, report } = data;
  const name = personal.name || report?.student?.name || "";
  const level = report?.student?.level_name || "";

  return (
    <>
      <div className="top-bar" style={{ justifyContent: "center", padding: "16px 18px 8px" }}>
        <Image
          src="/logo.svg"
          alt="شعار الجمعية"
          width={160}
          height={80}
          priority
          style={{ height: "auto", maxHeight: 70 }}
        />
      </div>

      <div className="card" style={{ margin: "8px 14px 13px" }}>
        <div className="card-label">معلومات الطالب</div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* اسم الطالب */}
          <InfoRow label="الاسم" value={name} bold />

          {/* الحلقة */}
          {report?.student?.episode_name && (
            <InfoRow label="الحلقة" value={report.student.episode_name} />
          )}

          {/* المنشأة */}
          {personal.institution_name && (
            <InfoRow label="المنشأة" value={personal.institution_name} />
          )}

          {/* المعلم */}
          {personal.teacher_name && (
            <InfoRow label="المعلم" value={personal.teacher_name} />
          )}

          {/* الخطة / المستوى */}
          {level && (
            <InfoRow label="الخطة" value={level} />
          )}
        </div>
      </div>
    </>
  );
}
