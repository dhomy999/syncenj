import "./admin.css";
import type { Metadata } from "next";
import { fetchStudentsRoster, type RosterStudent } from "@/lib/api";
import { isAuthed, isAdminConfigured } from "./auth";
import AdminLogin from "./AdminLogin";
import AdminCards from "./AdminCards";

export const metadata: Metadata = {
  title: "الإدارة · بطاقات الطلاب",
};

export default async function AdminPage() {
  if (!(await isAuthed())) {
    return <AdminLogin configured={isAdminConfigured()} />;
  }

  let students: RosterStudent[] = [];
  let error = "";
  try {
    students = await fetchStudentsRoster();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return <AdminCards students={students} error={error} />;
}
