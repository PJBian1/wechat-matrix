from datetime import datetime
from pydantic import BaseModel


class AccountOut(BaseModel):
    id: int
    authorizer_appid: str
    nick_name: str | None = None
    head_img: str | None = None
    user_name: str | None = None
    principal_name: str | None = None
    service_type: int | None = None
    verify_type: int | None = None
    qrcode_url: str | None = None
    display_name: str | None = None
    group_tag: str | None = None
    is_active: bool = True
    authorized_at: datetime | None = None

    model_config = {"from_attributes": True}


class AccountUpdate(BaseModel):
    display_name: str | None = None
    group_tag: str | None = None


class AuthorizeUrlOut(BaseModel):
    authorize_url: str
