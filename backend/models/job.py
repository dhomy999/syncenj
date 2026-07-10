from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Job(Base):
    """مهمة مجدولة."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))             # اسم المهمة
    type: Mapped[str] = mapped_column(String(50))              # sync_episodes | export_students
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)  # مثال: "0 6 * * *"
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # معاملات المهمة
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
