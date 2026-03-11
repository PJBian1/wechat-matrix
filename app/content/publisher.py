"""发布逻辑：文章 → 素材上传 → 草稿 → 发布/群发"""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.publish import PublishRecord
from app.wechat.api import wechat_api
from app.wechat.token_manager import token_manager

logger = logging.getLogger(__name__)


async def publish_article(db: AsyncSession, record: PublishRecord, article: Article):
    """执行单条发布任务

    流程：上传封面 → 创建草稿 → 发布/群发
    """
    try:
        record.status = "uploading"
        await db.commit()

        # 1. 获取 token
        token = await token_manager.get_authorizer_token(db, record.account_id)

        # 2. 创建草稿
        draft_article = {
            "title": article.title,
            "author": article.author or "",
            "digest": article.digest or "",
            "content": article.content_html or "",
            "thumb_media_id": article.thumb_media_id or "",
            "need_open_comment": 1 if article.need_open_comment else 0,
            "only_fans_can_comment": 1 if article.only_fans_can_comment else 0,
        }
        if article.content_source_url:
            draft_article["content_source_url"] = article.content_source_url

        result = await wechat_api.add_draft(token, [draft_article])

        if "media_id" not in result:
            record.status = "failed"
            record.fail_reason = f"创建草稿失败: {result.get('errmsg', str(result))}"
            await db.commit()
            return

        media_id = result["media_id"]
        record.wx_draft_media_id = media_id
        record.status = "drafted"
        await db.commit()

        # 3. 发布或群发
        if record.publish_type == "freepublish":
            pub_result = await wechat_api.freepublish(token, media_id)
            if "publish_id" in pub_result:
                record.publish_id = str(pub_result["publish_id"])
                record.status = "publishing"
            else:
                record.status = "failed"
                record.fail_reason = f"发布失败: {pub_result.get('errmsg', str(pub_result))}"

        elif record.publish_type == "mass_send":
            mass_result = await wechat_api.mass_send_all(token, media_id)
            if mass_result.get("errcode") == 0:
                record.msg_data_id = str(mass_result.get("msg_data_id", ""))
                record.status = "publishing"
            else:
                record.status = "failed"
                record.fail_reason = f"群发失败: {mass_result.get('errmsg', str(mass_result))}"

        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as e:
        logger.exception(f"Publish failed for record {record.id}")
        record.status = "failed"
        record.fail_reason = str(e)
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()
