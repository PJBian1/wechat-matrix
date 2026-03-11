from datetime import date
from pydantic import BaseModel


class OverviewOut(BaseModel):
    total_fans: int = 0
    daily_net_growth: int = 0
    daily_reads: int = 0
    active_accounts: int = 0
    total_accounts: int = 0


class AccountStatsOut(BaseModel):
    account_id: int
    nick_name: str | None = None
    cumulate_user: int | None = None
    new_user: int = 0
    cancel_user: int = 0
    net_growth: int = 0
    total_read_count: int = 0
    total_share_count: int = 0
    stat_date: date

    model_config = {"from_attributes": True}


class TopArticleOut(BaseModel):
    title: str | None = None
    article_url: str | None = None
    account_id: int
    nick_name: str | None = None
    int_page_read_count: int = 0
    share_count: int = 0
    add_to_fav_count: int = 0
    stat_date: date
