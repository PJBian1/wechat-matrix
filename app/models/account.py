from datetime import datetime
from sqlalchemy import String, Text, SmallInteger, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuthorizedAccount(Base):
    __tablename__ = "authorized_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    authorizer_appid: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # 公众号基本信息
    nick_name: Mapped[str | None] = mapped_column(String(128))
    head_img: Mapped[str | None] = mapped_column(Text)
    user_name: Mapped[str | None] = mapped_column(String(128))
    principal_name: Mapped[str | None] = mapped_column(String(128))
    service_type: Mapped[int | None] = mapped_column(SmallInteger)  # 0=订阅号 2=服务号
    verify_type: Mapped[int | None] = mapped_column(SmallInteger)
    qrcode_url: Mapped[str | None] = mapped_column(Text)

    # Token
    authorizer_access_token: Mapped[str | None] = mapped_column(Text)
    authorizer_refresh_token: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 授权功能集
    func_info: Mapped[dict | None] = mapped_column(JSON)
    business_info: Mapped[dict | None] = mapped_column(JSON)

    # 用户自定义
    display_name: Mapped[str | None] = mapped_column(String(128))
    group_tag: Mapped[str | None] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    authorized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
