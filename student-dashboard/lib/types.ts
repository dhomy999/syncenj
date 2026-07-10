export interface StudentPageData {
  personal: {
    name: string;
    id_number: string;
    nationality: string;
    gender: string;
    phone: string;
    institution_name: string;
    teacher_name: string;
  };
  report: {
    student: {
      name: string;
      episode_name: string;
      episode_period_name: string;
      institution_name: string;
      program_name: string;
      level_name: string;
      start_date: string;
      filter_range: string;
      report_title: string;
      remaining_days: number;
      progress: number;
      pages_summary: {
        total_pages: number;
        completed: number;
        remaining: number;
      };
    };
    rating: {
      rate: number;
      grade: string;
    };
    saved_pages: {
      required: number;
      recite: number;
      rating: number;
      pages_numbers: string;
      history_lessons: Array<{ text: string }>;
      statics: Array<{
        date_key: string;
        required: number;
        recite: number;
        percentage: number;
      }>;
    };
    revision_pages: {
      required: number;
      recite: number;
      rating: number;
      small_revision: { required: number; recite: number };
      history_lessons: Array<{ text: string }>;
    };
    attendece: {
      attend: number;
      absent: number;
      late: number;
      excused: number;
      rate: number;
      real_attend_count: number;
      real_episode_count: number;
    };
    date_range: {
      from_date: string;
      to_date: string;
    };
    study_year: {
      name: string;
    };
    points: {
      amount: number;
      visible: boolean;
    };
  };
  monthly_attendance: {
    attend: number;
    absent: number;
    late: number;
    excused: number;
    rate: number;
    real_attend_count: number;
    real_episode_count: number;
  };
  quran_progress: {
    total: number;
    completed: number;
    remaining: number;
    current_page: number;
    pages_numbers_raw: string;
    pages_per_day: number;
  };
  today_lessons: Record<string, unknown>;
  meta: {
    sub_url: string;
    enjazi_student_id: number;
    episode_id: number;
    period_range: string;
    date_of: string;
  };
}
