"""内容管理路由"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.article import Article
from app.models.publish import PublishRecord
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleOut, PublishRequest
from app.schemas.publish import PublishRecordOut
from app.content.md_converter import md_to_wechat_html
from app.content.publisher import publish_article

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=list[ArticleOut])
async def list_articles(
    status: str | None = None,
    category: str | None = None,
    limit: int = QueryParam(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Article).order_by(Article.created_at.desc())
    if status:
        query = query.where(Article.status == status)
    if category:
        query = query.where(Article.category == category)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ArticleOut)
async def create_article(data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    article = Article(**data.model_dump(exclude_none=True))

    # 自动转换 Markdown → HTML
    if article.content_md and not article.content_html:
        article.content_html = md_to_wechat_html(article.content_md)

    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put("/{article_id}", response_model=ArticleOut)
async def update_article(article_id: int, data: ArticleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(article, key, value)

    # 重新转换 HTML
    if "content_md" in update_data:
        article.content_html = md_to_wechat_html(article.content_md)

    article.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(article)
    return article


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()
    return {"detail": "Deleted"}


@router.post("/{article_id}/preview")
async def preview_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """预览文章 (MD→HTML)"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    html = md_to_wechat_html(article.content_md or "")
    return {"html": html}


@router.post("/{article_id}/publish", response_model=list[PublishRecordOut])
async def publish_to_accounts(
    article_id: int, data: PublishRequest, db: AsyncSession = Depends(get_db)
):
    """发布文章到指定账号"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if not article.content_html:
        if article.content_md:
            article.content_html = md_to_wechat_html(article.content_md)
        else:
            raise HTTPException(status_code=400, detail="Article has no content")

    records = []
    for account_id in data.account_ids:
        record = PublishRecord(
            article_id=article_id,
            account_id=account_id,
            publish_type=data.publish_type,
            scheduled_at=data.scheduled_at,
            status="pending",
        )
        db.add(record)
        records.append(record)

    await db.commit()

    # 立即发布（非排期）
    if not data.scheduled_at:
        for record in records:
            await db.refresh(record)
            await publish_article(db, record, article)

    # 刷新状态
    for record in records:
        await db.refresh(record)

    return records
