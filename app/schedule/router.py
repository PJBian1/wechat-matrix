"""排期管理路由"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.publish import PublishRecord
from app.models.article import Article
from app.models.account import AuthorizedAccount
from app.schemas.publish import PublishRecordOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("", response_model=list[PublishRecordOut])
async def list_scheduled(
    status: str | None = None,
    account_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """列出排期任务"""
    query = (
        select(PublishRecord)
        .where(PublishRecord.scheduled_at.isnot(None))
        .order_by(PublishRecord.scheduled_at)
    )
    if status:
        query = query.where(PublishRecord.status == status)
    if account_id:
        query = query.where(PublishRecord.account_id == account_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/calendar")
async def get_calendar(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
):
    """日历视图数据"""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    result = await db.execute(
        select(PublishRecord, Article.title, AuthorizedAccount.nick_name)
        .join(Article, PublishRecord.article_id == Article.id)
        .join(AuthorizedAccount, PublishRecord.account_id == AuthorizedAccount.id)
        .where(
            and_(
                PublishRecord.scheduled_at >= start,
                PublishRecord.scheduled_at < end,
            )
        )
        .order_by(PublishRecord.scheduled_at)
    )

    return [
        {
            "id": record.id,
            "article_id": record.article_id,
            "article_title": title,
            "account_id": record.account_id,
            "nick_name": nick_name,
            "scheduled_at": record.scheduled_at.isoformat() if record.scheduled_at else None,
            "publish_type": record.publish_type,
            "status": record.status,
        }
        for record, title, nick_name in result.all()
    ]


@router.put("/{record_id}")
async def update_schedule(
    record_id: int,
    scheduled_at: datetime,
    db: AsyncSession = Depends(get_db),
):
    """修改排期时间"""
    result = await db.execute(
        select(PublishRecord).where(PublishRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Only pending records can be rescheduled")

    record.scheduled_at = scheduled_at
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"detail": "Rescheduled"}


@router.delete("/{record_id}")
async def cancel_schedule(record_id: int, db: AsyncSession = Depends(get_db)):
    """取消排期"""
    result = await db.execute(
        select(PublishRecord).where(PublishRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Only pending records can be cancelled")

    await db.delete(record)
    await db.commit()
    return {"detail": "Cancelled"}
