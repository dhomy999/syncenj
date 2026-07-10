from datetime import datetime
from sqlalchemy import Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class JobLog(Base):
    """سجل كل تنفيذ لمهمة."""
    __tablename__ = "job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20))  # running | success | failed
    triggered_by: Mapped[str] = mapped_column(String(20), default="scheduler")  # scheduler | manual

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # ملخص النتيجة
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    job = relationship("Job", backref="logs")
