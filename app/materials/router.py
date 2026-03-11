"""素材管理路由"""

import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.material import Material
from app.wechat.api import wechat_api
from app.wechat.token_manager import token_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("")
async def list_materials(
    account_id: int | None = None,
    media_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Material).order_by(Material.created_at.desc())
    if account_id:
        query = query.where(Material.account_id == account_id)
    if media_type:
        query = query.where(Material.media_type == media_type)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    materials = result.scalars().all()
    return [
        {
            "id": m.id,
            "account_id": m.account_id,
            "media_type": m.media_type,
            "media_id": m.media_id,
            "wx_url": m.wx_url,
            "title": m.title,
            "file_name": m.file_name,
            "file_size": m.file_size,
            "created_at": m.created_at,
        }
        for m in materials
    ]


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    media_type: str = Form(default="image"),
    title: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """上传素材到本地 + 微信永久素材"""
    settings = get_settings()

    # 1. 保存到本地
    ext = os.path.splitext(file.filename or "")[1]
    local_name = f"{uuid.uuid4().hex}{ext}"
    local_dir = os.path.join(settings.upload_dir, media_type)
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, local_name)

    content = await file.read()
    with open(local_path, "wb") as f:
        f.write(content)

    # 2. 上传到微信
    token = await token_manager.get_authorizer_token(db, account_id)
    wx_result = await wechat_api.upload_permanent_material(
        token, media_type, local_path, title=title
    )

    if "media_id" not in wx_result:
        os.remove(local_path)
        raise HTTPException(status_code=400, detail=f"微信上传失败: {wx_result.get('errmsg', str(wx_result))}")

    # 3. 入库
    material = Material(
        account_id=account_id,
        media_type=media_type,
        media_id=wx_result.get("media_id"),
        wx_url=wx_result.get("url"),
        title=title or file.filename,
        file_name=file.filename,
        file_size=len(content),
        file_path=local_path,
        is_permanent=True,
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)

    return {
        "id": material.id,
        "media_id": material.media_id,
        "wx_url": material.wx_url,
        "file_name": material.file_name,
    }


@router.delete("/{material_id}")
async def delete_material(material_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # 删除本地文件
    if material.file_path and os.path.exists(material.file_path):
        os.remove(material.file_path)

    await db.delete(material)
    await db.commit()
    return {"detail": "Deleted"}


@router.post("/{material_id}/distribute")
async def distribute_material(
    material_id: int,
    target_account_ids: list[int],
    db: AsyncSession = Depends(get_db),
):
    """分发素材到其他账号"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    source = result.scalar_one_or_none()
    if not source or not source.file_path:
        raise HTTPException(status_code=404, detail="Source material not found")

    results = []
    for account_id in target_account_ids:
        try:
            token = await token_manager.get_authorizer_token(db, account_id)
            wx_result = await wechat_api.upload_permanent_material(
                token, source.media_type, source.file_path, title=source.title or ""
            )

            if "media_id" in wx_result:
                new_material = Material(
                    account_id=account_id,
                    media_type=source.media_type,
                    media_id=wx_result["media_id"],
                    wx_url=wx_result.get("url"),
                    title=source.title,
                    file_name=source.file_name,
                    file_size=source.file_size,
                    file_path=source.file_path,
                    is_permanent=True,
                    is_shared=True,
                    source_material_id=source.id,
                )
                db.add(new_material)
                results.append({"account_id": account_id, "status": "success", "media_id": wx_result["media_id"]})
            else:
                results.append({"account_id": account_id, "status": "failed", "error": wx_result.get("errmsg")})
        except Exception as e:
            results.append({"account_id": account_id, "status": "failed", "error": str(e)})

    await db.commit()
    return results
