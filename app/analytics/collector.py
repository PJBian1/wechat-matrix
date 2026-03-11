"""数据统计拉取"""

import logging
from datetime import datetime, timedelta, timezone, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import AuthorizedAccount
from app.models.stats import ArticleStats, AccountDailyStats
from app.wechat.api import wechat_api
from app.wechat.token_manager import token_manager

logger = logging.getLogger(__name__)


async def pull_daily_stats(db: AsyncSession, target_date: date | None = None):
    """拉取所有账号的前天统计数据"""
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=2)).date()

    date_str = target_date.strftime("%Y-%m-%d")
    logger.info(f"Pulling stats for {date_str}")

    result = await db.execute(
        select(AuthorizedAccount).where(AuthorizedAccount.is_active == True)
    )
    accounts = result.scalars().all()

    for account in accounts:
        try:
            token = await token_manager.get_authorizer_token(db, account.id)
            await _pull_account_stats(db, account, token, date_str)
        except Exception as e:
            logger.error(f"Pull stats failed for {account.nick_name}: {e}")

    logger.info(f"Stats pull completed for {date_str}")


async def _pull_account_stats(db: AsyncSession, account: AuthorizedAccount, token: str, date_str: str):
    """拉取单个账号的统计数据"""

    # 1. 用户增减
    user_data = await wechat_api.get_user_summary(token, date_str, date_str)
    user_cumulate = await wechat_api.get_user_cumulate(token, date_str, date_str)

    new_user = 0
    cancel_user = 0
    cumulate = None

    for item in user_data.get("list", []):
        new_user += item.get("new_user", 0)
        cancel_user += item.get("cancel_user", 0)

    for item in user_cumulate.get("list", []):
        cumulate = item.get("cumulate_user")

    # 2. 图文数据
    article_data = await wechat_api.get_article_total(token, date_str, date_str)

    total_reads = 0
    total_shares = 0

    for item in article_data.get("list", []):
        details = item.get("details", [])
        for detail in details:
            stat = detail.get("stat_info", {})
            reads = stat.get("int_page_read_count", 0)
            shares = stat.get("share_count", 0)
            favs = stat.get("add_to_fav_count", 0)

            total_reads += reads
            total_shares += shares

            # 文章级别入库
            article_stat = ArticleStats(
                account_id=account.id,
                stat_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                title=item.get("title"),
                article_url=detail.get("page_path"),
                int_page_read_user=stat.get("int_page_read_user", 0),
                int_page_read_count=reads,
                share_user=stat.get("share_user", 0),
                share_count=shares,
                add_to_fav_user=stat.get("add_to_fav_user", 0),
                add_to_fav_count=favs,
            )
            db.add(article_stat)

    # 3. 账号日统计入库
    daily_stat = AccountDailyStats(
        account_id=account.id,
        stat_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        new_user=new_user,
        cancel_user=cancel_user,
        cumulate_user=cumulate,
        net_growth=new_user - cancel_user,
        total_read_count=total_reads,
        total_share_count=total_shares,
    )
    db.add(daily_stat)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.warning(f"Stats for {account.nick_name} on {date_str} may already exist, skipping")
