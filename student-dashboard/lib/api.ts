import { StudentPageData } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchStudentPage(
  subUrl: string,
  periodRange: string = "W",
  dateOf: string = ""
): Promise<StudentPageData> {
  const params = new URLSearchParams({ period_range: periodRange });
  if (dateOf) params.set("date_of", dateOf);

  const res = await fetch(
    `${API_URL}/api/student-page/${subUrl}?${params.toString()}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch student data: ${res.status}`);
  }

  return res.json();
}

export interface RosterStudent {
  sub_url: string;
  student_number: string;
  name: string;
}

export async function fetchStudentsRoster(): Promise<RosterStudent[]> {
  const res = await fetch(`${API_URL}/api/data/students-roster`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch students roster: ${res.status}`);
  }

  const json = await res.json();
  return (json.data ?? []) as RosterStudent[];
}
