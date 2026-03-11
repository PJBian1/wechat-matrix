"""Token 管理：component_access_token + authorizer_access_token"""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import PlatformConfig
from app.models.account import AuthorizedAccount

logger = logging.getLogger(__name__)

WX_API_BASE = "https://api.weixin.qq.com"


class TokenManager:
    """微信 Token 全链路管理"""

    def __init__(self):
        self._component_token_cache: str | None = None
        self._component_token_expires: datetime | None = None
        self._authorizer_token_cache: dict[str, tuple[str, datetime]] = {}

    async def save_ticket(self, db: AsyncSession, ticket: str):
        """保存 component_verify_ticket"""
        result = await db.execute(select(PlatformConfig).limit(1))
        config = result.scalar_one_or_none()
        if config:
            config.component_verify_ticket = ticket
            config.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Saved component_verify_ticket")

    async def get_component_access_token(self, db: AsyncSession) -> str:
        """获取 component_access_token (带缓存)"""
        now = datetime.now(timezone.utc)

        # 内存缓存命中
        if self._component_token_cache and self._component_token_expires and now < self._component_token_expires:
            return self._component_token_cache

        # 从数据库检查
        result = await db.execute(select(PlatformConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError("Platform config not found")

        if config.component_access_token and config.component_token_expires_at:
            expires = config.component_token_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now < expires - timedelta(minutes=10):
                self._component_token_cache = config.component_access_token
                self._component_token_expires = expires
                return config.component_access_token

        # 重新获取
        if not config.component_verify_ticket:
            raise ValueError("No component_verify_ticket available")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WX_API_BASE}/cgi-bin/component/api_component_token",
                json={
                    "component_appid": config.component_appid,
                    "component_appsecret": config.component_appsecret,
                    "component_verify_ticket": config.component_verify_ticket,
                },
                timeout=10,
            )
            data = resp.json()

        if "component_access_token" not in data:
            raise ValueError(f"Failed to get component_access_token: {data}")

        token = data["component_access_token"]
        expires_in = data.get("expires_in", 7200)
        expires_at = now + timedelta(seconds=expires_in)

        # 更新数据库
        config.component_access_token = token
        config.component_token_expires_at = expires_at
        config.updated_at = now
        await db.commit()

        # 更新缓存
        self._component_token_cache = token
        self._component_token_expires = expires_at

        logger.info("Refreshed component_access_token")
        return token

    async def get_pre_auth_code(self, db: AsyncSession) -> str:
        """获取预授权码"""
        result = await db.execute(select(PlatformConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError("Platform config not found")

        component_token = await self.get_component_access_token(db)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WX_API_BASE}/cgi-bin/component/api_create_preauthcode",
                params={"component_access_token": component_token},
                json={"component_appid": config.component_appid},
                timeout=10,
            )
            data = resp.json()

        if "pre_auth_code" not in data:
            raise ValueError(f"Failed to get pre_auth_code: {data}")

        return data["pre_auth_code"]

    async def handle_authorization(self, db: AsyncSession, auth_code: str):
        """处理授权完成：交换 token + 获取账号信息"""
        result = await db.execute(select(PlatformConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            return

        component_token = await self.get_component_access_token(db)

        # 1. 用 auth_code 换取 authorizer_access_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WX_API_BASE}/cgi-bin/component/api_query_auth",
                params={"component_access_token": component_token},
                json={
                    "component_appid": config.component_appid,
                    "authorization_code": auth_code,
                },
                timeout=10,
            )
            auth_data = resp.json()

        auth_info = auth_data.get("authorization_info", {})
        appid = auth_info.get("authorizer_appid")
        if not appid:
            logger.error(f"Authorization failed: {auth_data}")
            return

        access_token = auth_info.get("authorizer_access_token")
        refresh_token = auth_info.get("authorizer_refresh_token")
        expires_in = auth_info.get("expires_in", 7200)
        func_info = auth_info.get("func_info", [])

        # 2. 获取公众号详细信息
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WX_API_BASE}/cgi-bin/component/api_get_authorizer_info",
                params={"component_access_token": component_token},
                json={
                    "component_appid": config.component_appid,
                    "authorizer_appid": appid,
                },
                timeout=10,
            )
            info_data = resp.json()

        authorizer_info = info_data.get("authorizer_info", {})
        now = datetime.now(timezone.utc)

        # 3. 入库 (upsert)
        existing = await db.execute(
            select(AuthorizedAccount).where(AuthorizedAccount.authorizer_appid == appid)
        )
        account = existing.scalar_one_or_none()

        if account:
            account.authorizer_access_token = access_token
            account.authorizer_refresh_token = refresh_token
            account.token_expires_at = now + timedelta(seconds=expires_in)
            account.nick_name = authorizer_info.get("nick_name")
            account.head_img = authorizer_info.get("head_img")
            account.user_name = authorizer_info.get("user_name")
            account.principal_name = authorizer_info.get("principal_name")
            account.service_type = authorizer_info.get("service_type_info", {}).get("id")
            account.verify_type = authorizer_info.get("verify_type_info", {}).get("id")
            account.qrcode_url = authorizer_info.get("qrcode_url")
            account.func_info = func_info
            account.business_info = authorizer_info.get("business_info")
            account.is_active = True
            account.updated_at = now
        else:
            account = AuthorizedAccount(
                authorizer_appid=appid,
                authorizer_access_token=access_token,
                authorizer_refresh_token=refresh_token,
                token_expires_at=now + timedelta(seconds=expires_in),
                nick_name=authorizer_info.get("nick_name"),
                head_img=authorizer_info.get("head_img"),
                user_name=authorizer_info.get("user_name"),
                principal_name=authorizer_info.get("principal_name"),
                service_type=authorizer_info.get("service_type_info", {}).get("id"),
                verify_type=authorizer_info.get("verify_type_info", {}).get("id"),
                qrcode_url=authorizer_info.get("qrcode_url"),
                func_info=func_info,
                business_info=authorizer_info.get("business_info"),
                authorized_at=now,
            )
            db.add(account)

        await db.commit()
        logger.info(f"Authorized account: {authorizer_info.get('nick_name')} ({appid})")

    async def refresh_authorizer_token(self, db: AsyncSession, account: AuthorizedAccount):
        """刷新单个账号的 authorizer_access_token"""
        result = await db.execute(select(PlatformConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            return

        component_token = await self.get_component_access_token(db)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WX_API_BASE}/cgi-bin/component/api_authorizer_token",
                params={"component_access_token": component_token},
                json={
                    "component_appid": config.component_appid,
                    "authorizer_appid": account.authorizer_appid,
                    "authorizer_refresh_token": account.authorizer_refresh_token,
                },
                timeout=10,
            )
            data = resp.json()

        if "authorizer_access_token" not in data:
            logger.error(f"Refresh token failed for {account.nick_name}: {data}")
            return

        now = datetime.now(timezone.utc)
        account.authorizer_access_token = data["authorizer_access_token"]
        account.authorizer_refresh_token = data["authorizer_refresh_token"]
        account.token_expires_at = now + timedelta(seconds=data.get("expires_in", 7200))
        account.updated_at = now
        await db.commit()

        # 更新缓存
        self._authorizer_token_cache[account.authorizer_appid] = (
            data["authorizer_access_token"],
            account.token_expires_at,
        )
        logger.info(f"Refreshed token for {account.nick_name}")

    async def get_authorizer_token(self, db: AsyncSession, account_id: int) -> str:
        """获取指定账号的 authorizer_access_token (带缓存)"""
        result = await db.execute(
            select(AuthorizedAccount).where(AuthorizedAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        now = datetime.now(timezone.utc)

        # 检查缓存
        if account.authorizer_appid in self._authorizer_token_cache:
            cached_token, cached_expires = self._authorizer_token_cache[account.authorizer_appid]
            if now < cached_expires - timedelta(minutes=10):
                return cached_token

        # 检查数据库中的 token 是否还有效
        if account.token_expires_at:
            expires = account.token_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now < expires - timedelta(minutes=10):
                self._authorizer_token_cache[account.authorizer_appid] = (
                    account.authorizer_access_token,
                    expires,
                )
                return account.authorizer_access_token

        # 需要刷新
        await self.refresh_authorizer_token(db, account)
        return account.authorizer_access_token


# 全局单例
token_manager = TokenManager()
