from datetime import datetime
from pydantic import BaseModel


class ArticleCreate(BaseModel):
    title: str
    author: str | None = None
    digest: str | None = None
    content_md: str | None = None
    content_html: str | None = None
    cover_material_id: int | None = None
    need_open_comment: bool = True
    only_fans_can_comment: bool = False
    content_source_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class ArticleUpdate(ArticleCreate):
    title: str | None = None


class ArticleOut(BaseModel):
    id: int
    title: str
    author: str | None = None
    digest: str | None = None
    content_md: str | None = None
    content_html: str | None = None
    cover_material_id: int | None = None
    thumb_media_id: str | None = None
    need_open_comment: bool
    only_fans_can_comment: bool
    content_source_url: str | None = None
    category: str | None = None
    tags: list | None = None
    status: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublishRequest(BaseModel):
    account_ids: list[int]
    publish_type: str = "freepublish"  # freepublish / mass_send
    scheduled_at: datetime | None = None
