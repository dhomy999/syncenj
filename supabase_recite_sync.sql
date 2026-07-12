-- ترقية جدول التسميع لدعم المزامنة المستمرة مع إنجازي.
-- آمنة للتشغيل أكثر من مرة (IF NOT EXISTS).
--
-- الفكرة: كل صف يحمل حالته الخاصة، فلا يمرّ العامل على الصفوف المُزامَنة مرّة أخرى
-- (هذا ما كان يستهلك ساعات: الاستعلام عن كل طالب في إنجازي لاكتشاف أنه مُسجَّل مسبقًا).

ALTER TABLE public.quran_recitation
    -- pending | synced | skipped | failed
    ADD COLUMN IF NOT EXISTS sync_status      text        NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS sync_attempts    integer     NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_attempt_at  timestamptz,
    ADD COLUMN IF NOT EXISTS synced_at        timestamptz,
    ADD COLUMN IF NOT EXISTS sync_error       text;

-- الصفوف التي زُومنت سابقًا (قبل وجود عمود الحالة) تُعلَّم synced حتى لا يعيد العامل معالجتها.
UPDATE public.quran_recitation
   SET sync_status = 'synced'
 WHERE synced_at IS NOT NULL
   AND sync_status = 'pending';

-- العامل يسحب المعلّق فقط، مرتّبًا بالتاريخ: فهرس على (sync_status, recite_date).
CREATE INDEX IF NOT EXISTS quran_recitation_sync_status_idx
    ON public.quran_recitation (sync_status, recite_date);
