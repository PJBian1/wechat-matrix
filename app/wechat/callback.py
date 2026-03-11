"""微信第三方平台回调路由"""

import logging

from fastapi import APIRouter, Request, Query, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.wechat.crypto import WeChatCrypto, parse_xml
from app.wechat.token_manager import token_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wechat", tags=["wechat-callback"])


def get_crypto() -> WeChatCrypto:
    settings = get_settings()
    return WeChatCrypto(
        token=settings.wx_verify_token,
        encoding_aes_key=settings.wx_encoding_aes_key,
        component_appid=settings.wx_component_appid,
    )


@router.post("/callback")
async def wechat_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    timestamp: str = Query(...),
    nonce: str = Query(...),
    msg_signature: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """授权事件接收 URL — 接收 ticket、授权、取消授权等事件"""
    crypto = get_crypto()
    body = await request.body()
    body_str = body.decode("utf-8")

    # 从 XML 提取 Encrypt 字段
    xml_data = parse_xml(body_str)
    encrypt = xml_data.get("Encrypt", "")

    if not encrypt:
        return PlainTextResponse("success")

    # 验签
    if not crypto.verify_signature(msg_signature, timestamp, nonce, encrypt):
        logger.warning("Signature verification failed")
        return PlainTextResponse("fail")

    # 解密
    decrypted_xml, appid = crypto.decrypt(encrypt)
    msg_data = parse_xml(decrypted_xml)
    info_type = msg_data.get("InfoType", "")

    logger.info(f"Received callback: InfoType={info_type}")

    if info_type == "component_verify_ticket":
        ticket = msg_data.get("ComponentVerifyTicket", "")
        if ticket:
            background_tasks.add_task(_save_ticket, ticket)

    elif info_type == "authorized":
        auth_code = msg_data.get("AuthorizationCode", "")
        if auth_code:
            background_tasks.add_task(_handle_auth, auth_code)

    elif info_type == "unauthorized":
        authorizer_appid = msg_data.get("AuthorizerAppid", "")
        if authorizer_appid:
            background_tasks.add_task(_handle_deauth, authorizer_appid)

    elif info_type == "updateauthorized":
        auth_code = msg_data.get("AuthorizationCode", "")
        if auth_code:
            background_tasks.add_task(_handle_auth, auth_code)

    # 必须 5 秒内返回 success
    return PlainTextResponse("success")


@router.get("/callback")
async def wechat_callback_verify(
    echostr: str = Query(default=""),
):
    """微信回调验证（GET 请求）"""
    return PlainTextResponse(echostr)


@router.post("/callback/{appid}")
async def wechat_message_callback(
    appid: str,
    request: Request,
    timestamp: str = Query(...),
    nonce: str = Query(...),
    msg_signature: str = Query(...),
):
    """消息/事件接收 URL — 接收粉丝消息等"""
    # 暂时只返回 success，后续扩展客服消息等功能
    return PlainTextResponse("success")


@router.get("/auth_callback")
async def auth_callback(
    auth_code: str = Query(...),
    expires_in: int = Query(default=3600),
):
    """授权完成回调 — 管理员扫码授权后跳转"""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await token_manager.handle_authorization(db, auth_code)

    # 重定向到前端账号管理页
    settings = get_settings()
    return PlainTextResponse(
        content="<html><body><h2>授权成功！</h2><p>正在跳转...</p>"
        f'<script>window.location.href="{settings.base_url}/admin/accounts"</script>'
        "</body></html>",
        media_type="text/html",
    )


# ─── Background tasks ────────────────────────────────

async def _save_ticket(ticket: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await token_manager.save_ticket(db, ticket)


async def _handle_auth(auth_code: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await token_manager.handle_authorization(db, auth_code)


async def _handle_deauth(authorizer_appid: str):
    from app.database import AsyncSessionLocal
    from sqlalchemy import update
    from app.models.account import AuthorizedAccount

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(AuthorizedAccount)
            .where(AuthorizedAccount.authorizer_appid == authorizer_appid)
            .values(is_active=False)
        )
        await db.commit()
        logger.info(f"Deauthorized: {authorizer_appid}")
