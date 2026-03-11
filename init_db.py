#!/usr/bin/env python3
"""数据库初始化：建表 + 插入 platform_config"""

import asyncio
from sqlalchemy import select
from app.config import get_settings
from app.database import engine, Base, AsyncSessionLocal

# 导入所有模型确保建表
from app.models.platform import PlatformConfig  # noqa
from app.models.account import AuthorizedAccount  # noqa
from app.models.material import Material  # noqa
from app.models.article import Article  # noqa
from app.models.publish import PublishRecord  # noqa
from app.models.stats import ArticleStats, AccountDailyStats  # noqa
from app.models.log import OperationLog  # noqa


async def init():
    settings = get_settings()

    # 建表（如果不存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    # 初始化 platform_config（仅在表为空时插入）
    if settings.wx_component_appid:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(PlatformConfig).limit(1))
            existing = result.scalar_one_or_none()
            if not existing:
                config = PlatformConfig(
                    component_appid=settings.wx_component_appid,
                    component_appsecret=settings.wx_component_appsecret,
                    encoding_aes_key=settings.wx_encoding_aes_key,
                    verify_token=settings.wx_verify_token,
                )
                db.add(config)
                await db.commit()
                print(f"Initialized platform_config: {settings.wx_component_appid}")
            else:
                # 更新凭证（环境变量可能变了）
                existing.component_appid = settings.wx_component_appid
                existing.component_appsecret = settings.wx_component_appsecret
                existing.encoding_aes_key = settings.wx_encoding_aes_key
                existing.verify_token = settings.wx_verify_token
                await db.commit()
                print(f"Updated platform_config: {settings.wx_component_appid}")


if __name__ == "__main__":
    asyncio.run(init())
