-- ================================================================
-- إنشاء جداول Supabase لنظام إنجازي
-- Create Tables for Enjazi Automation System
-- ================================================================

-- 1. جدول المهام (Jobs Table)
CREATE TABLE IF NOT EXISTS public.jobs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    cron_expression VARCHAR(100),
    params JSONB,
    is_active BOOLEAN DEFAULT true NOT NULL,
    description TEXT,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON public.jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at);

-- ================================================================

-- 2. جدول سجلات المهام (Job Logs Table)
CREATE TABLE IF NOT EXISTS public.job_logs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_id BIGINT NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    triggered_by VARCHAR(50),
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON public.job_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_status ON public.job_logs(status);
CREATE INDEX IF NOT EXISTS idx_job_logs_created_at ON public.job_logs(created_at);

-- ================================================================

-- 3. جدول الكاش (Data Cache Table)
CREATE TABLE IF NOT EXISTS public.data_cache (
    key VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================

-- 4. جدول واردات الطلاب (Student Imports Table)
CREATE TABLE IF NOT EXISTS public.student_imports (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_log_id BIGINT REFERENCES public.job_logs(id) ON DELETE CASCADE,
    student_data JSONB,
    import_status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_student_imports_job_log_id ON public.student_imports(job_log_id);
CREATE INDEX IF NOT EXISTS idx_student_imports_status ON public.student_imports(import_status);

-- ================================================================
-- انتهى إنشاء الجداول
-- ================================================================
