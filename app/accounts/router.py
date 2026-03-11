"""账号管理路由"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.account import AuthorizedAccount
from app.schemas.account import AccountOut, AccountUpdate, AuthorizeUrlOut
from app.wechat.token_manager import token_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/accounts", tags=["accounts"])

AUTH_PAGE_URL = "https://mp.weixin.qq.com/cgi-bin/componentloginpage"


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    active_only: bool = True,
    group_tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AuthorizedAccount).order_by(AuthorizedAccount.authorized_at.desc())
    if active_only:
        query = query.where(AuthorizedAccount.is_active == True)
    if group_tag:
        query = query.where(AuthorizedAccount.group_tag == group_tag)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/authorize", response_model=AuthorizeUrlOut)
async def get_authorize_url(db: AsyncSession = Depends(get_db)):
    """生成授权链接"""
    settings = get_settings()
    pre_auth_code = await token_manager.get_pre_auth_code(db)
    redirect_uri = f"{settings.base_url}/wechat/auth_callback"

    authorize_url = (
        f"{AUTH_PAGE_URL}"
        f"?component_appid={settings.wx_component_appid}"
        f"&pre_auth_code={pre_auth_code}"
        f"&redirect_uri={redirect_uri}"
        f"&auth_type=1"
    )
    return AuthorizeUrlOut(authorize_url=authorize_url)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuthorizedAccount).where(AuthorizedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int, data: AccountUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AuthorizedAccount).where(AuthorizedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(account, key, value)

    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}")
async def deactivate_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """停用账号（软删除）"""
    result = await db.execute(
        select(AuthorizedAccount).where(AuthorizedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.is_active = False
    await db.commit()
    return {"detail": "Deactivated"}


@router.post("/{account_id}/refresh-token")
async def refresh_token(account_id: int, db: AsyncSession = Depends(get_db)):
    """手动刷新账号 Token"""
    result = await db.execute(
        select(AuthorizedAccount).where(AuthorizedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await token_manager.refresh_authorizer_token(db, account)
    return {"detail": "Token refreshed"}
