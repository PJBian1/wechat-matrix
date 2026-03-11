from datetime import datetime
from pydantic import BaseModel


class PublishRecordOut(BaseModel):
    id: int
    article_id: int
    account_id: int
    publish_type: str
    status: str
    article_url: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    fail_reason: str | None = None
    sent_count: int | None = None
    error_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
