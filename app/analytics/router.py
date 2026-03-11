"""数据分析路由"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import AuthorizedAccount
from app.models.stats import ArticleStats, AccountDailyStats
from app.schemas.analytics import OverviewOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewOut)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """矩阵概览"""
    # 总账号数
    total = await db.execute(
        select(func.count(AuthorizedAccount.id)).where(AuthorizedAccount.is_active == True)
    )
    total_accounts = total.scalar() or 0

    # 最近一天有数据的日期
    latest_date = await db.execute(
        select(func.max(AccountDailyStats.stat_date))
    )
    latest = latest_date.scalar()

    if not latest:
        return OverviewOut(total_accounts=total_accounts, active_accounts=total_accounts)

    # 汇总当天数据
    stats = await db.execute(
        select(
            func.sum(AccountDailyStats.cumulate_user),
            func.sum(AccountDailyStats.net_growth),
            func.sum(AccountDailyStats.total_read_count),
            func.count(AccountDailyStats.id),
        ).where(AccountDailyStats.stat_date == latest)
    )
    row = stats.one()

    return OverviewOut(
        total_fans=row[0] or 0,
        daily_net_growth=row[1] or 0,
        daily_reads=row[2] or 0,
        active_accounts=row[3] or 0,
        total_accounts=total_accounts,
    )


@router.get("/accounts")
async def get_account_stats(
    start: date | None = None,
    end: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """各号统计对比"""
    if not end:
        result = await db.execute(select(func.max(AccountDailyStats.stat_date)))
        end = result.scalar() or date.today()
    if not start:
        start = end - timedelta(days=7)

    query = (
        select(
            AccountDailyStats.account_id,
            AuthorizedAccount.nick_name,
            func.max(AccountDailyStats.cumulate_user).label("cumulate_user"),
            func.sum(AccountDailyStats.new_user).label("new_user"),
            func.sum(AccountDailyStats.cancel_user).label("cancel_user"),
            func.sum(AccountDailyStats.net_growth).label("net_growth"),
            func.sum(AccountDailyStats.total_read_count).label("total_read_count"),
            func.sum(AccountDailyStats.total_share_count).label("total_share_count"),
        )
        .join(AuthorizedAccount, AccountDailyStats.account_id == AuthorizedAccount.id)
        .where(AccountDailyStats.stat_date.between(start, end))
        .group_by(AccountDailyStats.account_id, AuthorizedAccount.nick_name)
        .order_by(desc("total_read_count"))
    )

    result = await db.execute(query)
    return [
        {
            "account_id": row[0],
            "nick_name": row[1],
            "cumulate_user": row[2],
            "new_user": row[3],
            "cancel_user": row[4],
            "net_growth": row[5],
            "total_read_count": row[6],
            "total_share_count": row[7],
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        for row in result.all()
    ]


@router.get("/account/{account_id}/trend")
async def get_account_trend(
    account_id: int,
    start: date | None = None,
    end: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """单号趋势数据"""
    if not end:
        end = date.today()
    if not start:
        start = end - timedelta(days=30)

    result = await db.execute(
        select(AccountDailyStats)
        .where(
            AccountDailyStats.account_id == account_id,
            AccountDailyStats.stat_date.between(start, end),
        )
        .order_by(AccountDailyStats.stat_date)
    )

    stats = result.scalars().all()
    return [
        {
            "date": s.stat_date.isoformat(),
            "cumulate_user": s.cumulate_user,
            "new_user": s.new_user,
            "cancel_user": s.cancel_user,
            "net_growth": s.net_growth,
            "total_read_count": s.total_read_count,
            "total_share_count": s.total_share_count,
        }
        for s in stats
    ]


@router.get("/articles/top")
async def get_top_articles(
    days: int = Query(default=7, le=30),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """爆文排行"""
    cutoff = date.today() - timedelta(days=days)

    result = await db.execute(
        select(
            ArticleStats.title,
            ArticleStats.article_url,
            ArticleStats.account_id,
            AuthorizedAccount.nick_name,
            func.sum(ArticleStats.int_page_read_count).label("reads"),
            func.sum(ArticleStats.share_count).label("shares"),
            func.sum(ArticleStats.add_to_fav_count).label("favs"),
        )
        .join(AuthorizedAccount, ArticleStats.account_id == AuthorizedAccount.id)
        .where(ArticleStats.stat_date >= cutoff)
        .group_by(
            ArticleStats.title,
            ArticleStats.article_url,
            ArticleStats.account_id,
            AuthorizedAccount.nick_name,
        )
        .order_by(desc("reads"))
        .limit(limit)
    )

    return [
        {
            "title": row[0],
            "article_url": row[1],
            "account_id": row[2],
            "nick_name": row[3],
            "reads": row[4],
            "shares": row[5],
            "favs": row[6],
        }
        for row in result.all()
    ]
