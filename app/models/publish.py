from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PublishRecord(Base):
    __tablename__ = "publish_records"
    __table_args__ = (
        UniqueConstraint("article_id", "account_id", "publish_type", name="uq_publish_article_account"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("authorized_accounts.id"), index=True)

    # 微信侧信息
    wx_draft_media_id: Mapped[str | None] = mapped_column(String(128))
    publish_type: Mapped[str] = mapped_column(String(16))  # freepublish / mass_send
    publish_id: Mapped[str | None] = mapped_column(String(128))
    article_id_wx: Mapped[str | None] = mapped_column(String(128))
    article_url: Mapped[str | None] = mapped_column(Text)

    # 排期
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 状态: pending / uploading / drafted / publishing / published / failed
    status: Mapped[str] = mapped_column(String(32), default="pending")
    fail_reason: Mapped[str | None] = mapped_column(Text)

    # 群发相关
    msg_data_id: Mapped[str | None] = mapped_column(String(128))
    sent_count: Mapped[int | None] = mapped_column(Integer)
    error_count: Mapped[int | None] = mapped_column(Integer)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
