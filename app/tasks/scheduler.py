"""APScheduler 定时任务"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.models.account import AuthorizedAccount
from app.models.publish import PublishRecord
from app.models.article import Article
from app.wechat.token_manager import token_manager
from app.analytics.collector import pull_daily_stats
from app.content.publisher import publish_article

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def refresh_all_tokens():
    """刷新所有活跃账号的 authorizer_access_token"""
    logger.info("Starting token refresh for all accounts")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AuthorizedAccount).where(AuthorizedAccount.is_active == True)
        )
        accounts = result.scalars().all()

        for account in accounts:
            try:
                await token_manager.refresh_authorizer_token(db, account)
            except Exception as e:
                logger.error(f"Token refresh failed for {account.nick_name}: {e}")

    logger.info(f"Token refresh completed for {len(accounts)} accounts")


async def pull_stats():
    """拉取统计数据"""
    logger.info("Starting daily stats pull")
    async with AsyncSessionLocal() as db:
        await pull_daily_stats(db)


async def check_scheduled_publish():
    """检查到期的排期发布任务"""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PublishRecord).where(
                and_(
                    PublishRecord.status == "pending",
                    PublishRecord.scheduled_at.isnot(None),
                    PublishRecord.scheduled_at <= now,
                )
            )
        )
        records = result.scalars().all()

        for record in records:
            try:
                article_result = await db.execute(
                    select(Article).where(Article.id == record.article_id)
                )
                article = article_result.scalar_one_or_none()
                if article:
                    logger.info(f"Executing scheduled publish: record={record.id}")
                    await publish_article(db, record, article)
            except Exception as e:
                logger.error(f"Scheduled publish failed for record {record.id}: {e}")


def start_scheduler():
    """启动定时任务"""
    # 每 90 分钟刷新 Token
    scheduler.add_job(
        refresh_all_tokens,
        trigger=IntervalTrigger(minutes=90),
        id="refresh_tokens",
        replace_existing=True,
    )

    # 每天凌晨 3 点拉取前天数据
    scheduler.add_job(
        pull_stats,
        trigger=CronTrigger(hour=3, minute=0),
        id="pull_stats",
        replace_existing=True,
    )

    # 每分钟检查排期发布
    scheduler.add_job(
        check_scheduled_publish,
        trigger=IntervalTrigger(minutes=1),
        id="check_scheduled",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 3 jobs")


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
