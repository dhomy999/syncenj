-- ================================================================
-- ترحيل سكيمة Supabase لربط إنجازي (جسر مزامنة Supabase → إنجازي)
-- شغّل هذا الملف في: Supabase SQL Editor
-- عميل REST لا ينفّذ DDL، لذا يُشغَّل يدويًا مرة واحدة.
-- ================================================================

-- ── (1) أعمدة الربط بإنجازي ──────────────────────────────────────
-- تخزّن معرّف الكيان المقابل في إنجازي (student_id / episode_id).
ALTER TABLE public.students ADD COLUMN IF NOT EXISTS enjazi_id BIGINT;
ALTER TABLE public.halaqat  ADD COLUMN IF NOT EXISTS enjazi_id BIGINT;

CREATE INDEX IF NOT EXISTS idx_students_enjazi_id ON public.students(enjazi_id);
CREATE INDEX IF NOT EXISTS idx_halaqat_enjazi_id  ON public.halaqat(enjazi_id);

-- ── (2) تتبّع مزامنة التسميع (quran_recitation → إنجازي) ──────────
-- synced_at: وقت الرفع الناجح لإنجازي (NULL = لم يُرفع بعد)
-- sync_error: رسالة الخطأ عند فشل الرفع
ALTER TABLE public.quran_recitation ADD COLUMN IF NOT EXISTS synced_at  TIMESTAMPTZ;
ALTER TABLE public.quran_recitation ADD COLUMN IF NOT EXISTS sync_error TEXT;

CREATE INDEX IF NOT EXISTS idx_recitation_unsynced
  ON public.quran_recitation(recite_date)
  WHERE synced_at IS NULL;

-- ================================================================
-- (3) الجداول التشغيلية (Phase 6 — اختياري الآن)
-- تُنقل من SQLite. أزِل التعليق عند تنفيذ Phase 6.
-- ================================================================
-- CREATE TABLE IF NOT EXISTS public.jobs (
--     id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
--     name VARCHAR(200) NOT NULL,
--     type VARCHAR(50) NOT NULL,
--     cron_expression VARCHAR(100),
--     params JSONB,
--     is_active BOOLEAN DEFAULT true NOT NULL,
--     description TEXT,
--     last_run_at TIMESTAMPTZ,
--     next_run_at TIMESTAMPTZ,
--     created_at TIMESTAMPTZ DEFAULT now(),
--     updated_at TIMESTAMPTZ DEFAULT now()
-- );
-- CREATE TABLE IF NOT EXISTS public.job_logs (
--     id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
--     job_id BIGINT NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
--     status VARCHAR(20) NOT NULL,
--     triggered_by VARCHAR(20),
--     started_at TIMESTAMPTZ DEFAULT now(),
--     finished_at TIMESTAMPTZ,
--     result JSONB,
--     error_message TEXT
-- );
-- CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON public.job_logs(job_id);
