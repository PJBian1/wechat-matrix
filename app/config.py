from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "公众号矩阵管理系统"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    admin_password: str = "admin"
    base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wechat_matrix"

    # WeChat Open Platform (第三方平台)
    wx_component_appid: str = ""
    wx_component_appsecret: str = ""
    wx_encoding_aes_key: str = ""
    wx_verify_token: str = ""

    # Feishu notification (optional)
    feishu_webhook_url: str = ""

    # Upload
    upload_dir: str = "/data/uploads"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
