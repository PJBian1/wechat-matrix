from datetime import datetime, date
from sqlalchemy import String, Text, Integer, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ArticleStats(Base):
    __tablename__ = "article_stats"
    __table_args__ = (
        UniqueConstraint("account_id", "stat_date", "article_url", name="uq_article_stats"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("authorized_accounts.id"), index=True)
    publish_record_id: Mapped[int | None] = mapped_column(ForeignKey("publish_records.id"))
    stat_date: Mapped[date] = mapped_column(Date, index=True)

    article_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(256))

    # 核心指标
    int_page_read_user: Mapped[int] = mapped_column(Integer, default=0)
    int_page_read_count: Mapped[int] = mapped_column(Integer, default=0)
    share_user: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    add_to_fav_user: Mapped[int] = mapped_column(Integer, default=0)
    add_to_fav_count: Mapped[int] = mapped_column(Integer, default=0)

    # 来源
    feed_share_from_feed_cnt: Mapped[int] = mapped_column(Integer, default=0)
    feed_share_from_timeline_cnt: Mapped[int] = mapped_column(Integer, default=0)
    feed_share_from_others_cnt: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AccountDailyStats(Base):
    __tablename__ = "account_daily_stats"
    __table_args__ = (
        UniqueConstraint("account_id", "stat_date", name="uq_daily_stats"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("authorized_accounts.id"), index=True)
    stat_date: Mapped[date] = mapped_column(Date, index=True)

    # 用户增减
    new_user: Mapped[int] = mapped_column(Integer, default=0)
    cancel_user: Mapped[int] = mapped_column(Integer, default=0)
    cumulate_user: Mapped[int | None] = mapped_column(Integer)
    net_growth: Mapped[int] = mapped_column(Integer, default=0)

    # 消息
    msg_count: Mapped[int] = mapped_column(Integer, default=0)

    # 阅读汇总
    total_read_count: Mapped[int] = mapped_column(Integer, default=0)
    total_share_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
