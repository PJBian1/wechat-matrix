from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlatformConfig(Base):
    __tablename__ = "platform_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_appid: Mapped[str] = mapped_column(String(64))
    component_appsecret: Mapped[str] = mapped_column(String(128))
    encoding_aes_key: Mapped[str] = mapped_column(String(64))
    verify_token: Mapped[str] = mapped_column(String(64))

    component_verify_ticket: Mapped[str | None] = mapped_column(Text, default=None)
    component_access_token: Mapped[str | None] = mapped_column(Text, default=None)
    component_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
