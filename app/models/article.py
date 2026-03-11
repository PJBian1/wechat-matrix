from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 内容
    title: Mapped[str] = mapped_column(String(256))
    author: Mapped[str | None] = mapped_column(String(64))
    digest: Mapped[str | None] = mapped_column(String(256))
    content_md: Mapped[str | None] = mapped_column(Text)
    content_html: Mapped[str | None] = mapped_column(Text)
    cover_material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"))
    thumb_media_id: Mapped[str | None] = mapped_column(String(128))
    need_open_comment: Mapped[bool] = mapped_column(Boolean, default=True)
    only_fans_can_comment: Mapped[bool] = mapped_column(Boolean, default=False)
    content_source_url: Mapped[str | None] = mapped_column(Text)

    # 分类标签
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    tags: Mapped[dict | None] = mapped_column(JSON, default=list)

    # 状态: draft / ready / publishing / published / failed
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    created_by: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
