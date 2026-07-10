from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class StudentImport(Base):
    """تتبع كل طالب في عملية استيراد."""
    __tablename__ = "student_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_logs.id", ondelete="CASCADE"), index=True)

    student_username: Mapped[str] = mapped_column(String(50))   # رقم الهوية
    student_name: Mapped[str] = mapped_column(String(200))
    episode_id: Mapped[str] = mapped_column(String(20))
    institution_id: Mapped[str] = mapped_column(String(20))

    status: Mapped[str] = mapped_column(String(20))             # success | failed | skipped
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    log = relationship("JobLog", backref="student_imports")
