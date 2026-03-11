from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("authorized_accounts.id"), index=True)

    media_type: Mapped[str] = mapped_column(String(16))  # image/voice/video/thumb
    media_id: Mapped[str | None] = mapped_column(String(128))
    wx_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(256))
    file_name: Mapped[str | None] = mapped_column(String(256))
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_path: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=True)

    # 跨号共享
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    source_material_id: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
