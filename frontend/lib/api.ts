import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// للطلبات البطيئة (جلب بيانات من إنجازي)
const apiSlow = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 300000,
});

// --- Types ---
export type JobType =
  | "add_students"
  | "open_episodes"
  | "sync_attend100"
  | "assign_level"
  | "teacher_recite"
  | "sync_students"
  | "sync_recitation"
  | "sync_episodes"
  | "export_students"
  | "register_students"
  | "sync_register_students";

export interface Job {
  id: number;
  name: string;
  type: JobType;
  cron_expression: string | null;
  params: Record<string, unknown> | null;
  description: string | null;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

export interface JobLog {
  id: number;
  job_id: number;
  status: "running" | "success" | "failed";
  triggered_by: "scheduler" | "manual";
  started_at: string;
  finished_at: string | null;
  result: Record<string, unknown> | null;
  error_message: string | null;
}

export interface StudentImport {
  id: number;
  student_username: string;
  student_name: string;
  episode_id: string;
  status: "success" | "failed" | "skipped";
  error: string | null;
  created_at: string;
}

// --- API helpers ---
export const jobsApi = {
  list: ()                   => api.get<Job[]>("/api/jobs"),
  create: (data: Partial<Job>) => api.post<Job>("/api/jobs", data),
  update: (id: number, data: Partial<Job>) => api.patch<Job>(`/api/jobs/${id}`, data),
  delete: (id: number)       => api.delete(`/api/jobs/${id}`),
  run:    (id: number)       => api.post(`/api/jobs/${id}/run`),
};

export const logsApi = {
  list: (params?: { job_id?: number; status?: string; limit?: number }) =>
    api.get<JobLog[]>("/api/logs", { params }),
  get:  (id: number) => api.get<JobLog>(`/api/logs/${id}`),
  students: (id: number) => api.get<StudentImport[]>(`/api/logs/${id}/students`),
};

export interface CachedResponse {
  data: Record<string, unknown>[];
  total: number;
  updated_at: string | null;
}

// --- Supabase-backed (المصدر) ---
export interface ListResponse<T> {
  data: T[];
  total: number;
}

export interface Halqa {
  id: string;
  halqa_code: string;
  track: string | null;
  period: string | null;
  circle_type: string | null;
  status: string | null;
  teacher_emp_no: number | null;
  teacher_name: string | null;
  enjazi_id: number | null;
  linked: boolean;
}

export interface SupaStudent {
  id: string;
  student_number: number;
  student_name: string;
  student_national_id: string;
  department: string | null;
  category: string | null;
  status: string | null;
  enjazi_id: number | null;
  linked: boolean;
  halaqat: string[];
}

export interface EnjaziEpisode {
  id: number;
  name: string;
  teacher_name: string | null;
}

export const halaqatApi = {
  list: () => api.get<ListResponse<Halqa>>("/api/halaqat"),
  link: (id: string, enjazi_id: number | null) =>
    api.patch(`/api/halaqat/${id}/link`, { enjazi_id }),
  enjaziEpisodes: (refresh = false) =>
    apiSlow.get<ListResponse<EnjaziEpisode> & { cached: boolean }>(
      "/api/halaqat/enjazi-episodes",
      { params: { refresh } }
    ),
};

export const studentsApi = {
  list: (params?: { linked?: boolean; search?: string; limit?: number }) =>
    api.get<ListResponse<SupaStudent>>("/api/students", { params }),
};

export const dataApi = {
  branches:          ()              => api.get<CachedResponse>("/api/data/branches"),
  facilities:        ()              => api.get<CachedResponse>("/api/data/facilities"),
  episodes:          ()              => api.get<CachedResponse>("/api/data/episodes"),
  students:          ()              => api.get<CachedResponse>("/api/data/students"),
  teachers:          ()              => api.get<CachedResponse>("/api/data/teachers"),
  refreshBranches:   ()              => apiSlow.post<CachedResponse>("/api/data/branches/refresh"),
  refreshFacilities: ()              => apiSlow.post<CachedResponse>("/api/data/facilities/refresh"),
  refreshEpisodes:   ()              => apiSlow.post<CachedResponse>("/api/data/episodes/refresh"),
  refreshStudents:   ()              => apiSlow.post<CachedResponse>("/api/data/students/refresh"),
  refreshTeachers:   ()              => apiSlow.post<CachedResponse>("/api/data/teachers/refresh"),
};
