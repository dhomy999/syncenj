from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import SessionLocal
from backend.models.job import Job
from enjazi.utils.logger import logger

scheduler = AsyncIOScheduler(timezone="Asia/Riyadh")


def _get_job_runner(job_type: str):
    """Return the async function for a given job type."""
    from backend.jobs.sync_episodes import run as sync_episodes
    from backend.jobs.export_students import run as export_students
    from backend.jobs.sync_students import run as sync_students
    from backend.jobs.register_students import run as register_students
    from backend.jobs.sync_register_students import run as sync_register_students
    from backend.jobs.sync_recitation import run as sync_recitation
    from backend.jobs.add_students import run as add_students
    from backend.jobs.open_episodes import run as open_episodes
    from backend.jobs.sync_attend100 import run as sync_attend100
    from backend.jobs.assign_level import run as assign_level

    runners = {
        "sync_episodes":        sync_episodes,
        "export_students":      export_students,
        "sync_students":        sync_students,
        "register_students":    register_students,
        "sync_register_students": sync_register_students,
        "sync_recitation":      sync_recitation,
        # العمليات الثلاث الرئيسية
        "add_students":         add_students,      # 1) تسجيل الطلاب الجدد
        "open_episodes":        open_episodes,     # 2) فتح الحلقات من جهة المعلم
        "sync_attend100":       sync_attend100,    # 3) مزامنة الحضور attend100
        # إسناد مستوى موحّد للطلاب بلا خطة (يُنشئ خطة التسميع)
        "assign_level":         assign_level,
    }
    return runners.get(job_type)


async def execute_job(job_id: int, triggered_by: str = "scheduler"):
    """Execute a job by ID and record the log."""
    from backend.models.job_log import JobLog

    db: Session = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Create log entry
        log = JobLog(job_id=job_id, status="running", triggered_by=triggered_by)
        db.add(log)
        db.commit()
        db.refresh(log)

        logger.info(f"Running job [{job.name}] (id={job_id}, trigger={triggered_by})")

        runner = _get_job_runner(job.type)
        if not runner:
            log.status = "failed"
            log.error_message = f"Unknown job type: {job.type}"
            log.finished_at = datetime.utcnow()
            db.commit()
            return

        try:
            result = await runner(job.params or {}, log_id=log.id, db=db)
            log.status = "success"
            log.result = result
        except Exception as exc:
            logger.error(f"Job [{job.name}] failed: {exc}")
            log.status = "failed"
            log.error_message = str(exc)

        log.finished_at = datetime.utcnow()
        job.last_run_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()


def load_jobs_from_db():
    """Load all active jobs from DB into the scheduler on startup."""
    db: Session = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.is_active == True, Job.cron_expression != None).all()  # noqa
        for job in jobs:
            try:
                _schedule_job(job)
            except Exception as exc:
                logger.warning(f"تعذّر جدولة المهمة [{job.name}] (cron: {job.cron_expression}): {exc}")
        logger.info(f"Loaded {len(jobs)} scheduled jobs from DB")
    finally:
        db.close()


def _schedule_job(job: Job):
    """Add or replace a job in APScheduler."""
    scheduler_job_id = f"job_{job.id}"
    scheduler.add_job(
        execute_job,
        trigger=CronTrigger.from_crontab(job.cron_expression, timezone="Asia/Riyadh"),
        id=scheduler_job_id,
        args=[job.id],
        replace_existing=True,
        name=job.name,
    )
    logger.info(f"Scheduled job [{job.name}] -> cron: {job.cron_expression}")


def add_or_update_job(job: Job):
    """Called after creating/updating a job via API."""
    if job.is_active and job.cron_expression:
        _schedule_job(job)
    else:
        remove_job(job.id)


def remove_job(job_id: int):
    """Remove a job from the scheduler."""
    scheduler_job_id = f"job_{job_id}"
    if scheduler.get_job(scheduler_job_id):
        scheduler.remove_job(scheduler_job_id)
        logger.info(f"Removed job {job_id} from scheduler")


# ─── المهام الافتراضية (تُنشأ تلقائياً عند الإقلاع إن لم توجد) ────────────────
# تُشحن العمليتان 2 و3 بـ dry_run=True؛ تُفعّل بعد التحقق عبر PATCH /api/jobs/{id}.
# أيام السبت–الخميس (عدا الجمعة) بأسماء الأيام لتفادي اختلاف ترقيم dow بين إصدارات APScheduler.
DEFAULT_JOBS = [
    {
        "type": "add_students",
        "name": "تسجيل الطلاب الجدد فردياً (1 ص)",
        "cron_expression": "0 1 * * *",
        "description": (
            "يجلب طلاب Supabase بلا enjazi_id في حلقة مربوطة، يسجّلهم فرديًا في إنجازي "
            "(check-username ثم إنشاء/إعادة تسجيل) ويكتب enjazi_id عائدًا."
        ),
        "params": {"limit": 50},
    },
    {
        "type": "open_episodes",
        "name": "فتح الحلقات من جهة المعلم (4 ص، عدا الجمعة)",
        "cron_expression": "0 4 * * sat,sun,mon,tue,wed,thu",
        "description": (
            "يفتح كل حلقة نشطة لليوم بتحضير طالب واحد من حساب المعلم الإشرافي (apps/v1). "
            "يُشحن dry_run=True — فعّله بعد ضبط بيانات حساب المعلم في .env والتحقق."
        ),
        "params": {"dry_run": True},
    },
    {
        "type": "sync_attend100",
        "name": "مزامنة الحضور attend100 (كل ساعة 5ص–10م)",
        "cron_expression": "0 5-22 * * *",
        "description": (
            "يعلّم كل طالب له سجل تسميع اليوم في Supabase حاضرًا في إنجازي (attend_type=attend100، "
            "lessons=[]) ويكتب synced_at. يُشحن dry_run=True — فعّله بعد التحقق."
        ),
        "params": {"dry_run": True},
    },
    {
        "type": "assign_level",
        "name": "إسناد المستوى للطلاب بلا خطة (يدوي)",
        "cron_expression": None,  # يدوي فقط — يُشغّل من زر «تشغيل»
        "description": (
            "يُسند مستوى موحّدًا (level_id=1745) لكل طالب لا خطة تسميع له، فيُنشئ الخطة تلقائيًا "
            "(change-level) ويحل خطأ chain_id on null. يفحص كل طالب ولا يلمس من عنده خطة. "
            "يُشحن dry_run=True — شغّله تجريبيًا أولًا ثم حوّله إلى «مباشر»."
        ),
        "params": {"dry_run": True},
    },
]

# أنواع مهام افتراضية قديمة تُعطَّل عند الإقلاع (استُبدلت بالعمليات الثلاث أعلاه).
DEPRECATED_DEFAULT_TYPES = {"sync_register_students"}


def ensure_default_jobs():
    """إنشاء المهام الافتراضية في قاعدة البيانات وجدولتها (idempotent)."""
    db: Session = SessionLocal()
    try:
        # تعطيل المهام الافتراضية القديمة (النوع يبقى متاحًا للتشغيل اليدوي والسجلات).
        for old in db.query(Job).filter(
            Job.type.in_(DEPRECATED_DEFAULT_TYPES), Job.is_active == True  # noqa: E712
        ).all():
            old.is_active = False
            db.commit()
            remove_job(old.id)
            logger.info(f"عُطّلت المهمة الافتراضية القديمة [{old.name}] (type={old.type})")

        for spec in DEFAULT_JOBS:
            existing = db.query(Job).filter(Job.type == spec["type"]).first()
            if existing:
                continue
            job = Job(
                name=spec["name"],
                type=spec["type"],
                cron_expression=spec["cron_expression"],
                params=spec.get("params"),
                description=spec.get("description"),
                is_active=True,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            if not job.cron_expression:
                logger.info(f"Seeded manual default job [{job.name}] (بلا جدولة)")
                continue
            try:
                _schedule_job(job)
                logger.info(f"Seeded default job [{job.name}] -> cron: {job.cron_expression}")
            except Exception as exc:
                logger.warning(f"تعذّر جدولة المهمة الافتراضية [{job.name}]: {exc}")
    finally:
        db.close()
