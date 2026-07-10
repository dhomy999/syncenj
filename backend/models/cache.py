from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class DataCache(Base):
    """كاش محلي للبيانات المجلوبة من Injazi API."""
    __tablename__ = "data_cache"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    # القيم: "students" | "episodes" | "branches" | "facilities" | "teachers"
    data: Mapped[list | dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
