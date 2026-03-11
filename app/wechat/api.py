"""微信公众号 API 封装"""

import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

WX_API_BASE = "https://api.weixin.qq.com"
WX_UPLOAD_BASE = "https://api.weixin.qq.com"


class WeChatAPI:
    """微信公众号 API 调用封装"""

    def __init__(self):
        self.timeout = 30

    # ─── 素材管理 ─────────────────────────────────────

    async def upload_permanent_material(
        self, token: str, media_type: str, file_path: str, title: str = "", description: str = ""
    ) -> dict:
        """上传永久素材 (图片/视频/音频/缩略图)"""
        url = f"{WX_API_BASE}/cgi-bin/material/add_material"
        params = {"access_token": token, "type": media_type}

        path = Path(file_path)
        async with httpx.AsyncClient() as client:
            files = {"media": (path.name, open(file_path, "rb"))}
            data = {}
            if media_type == "video":
                import json
                data["description"] = json.dumps({"title": title, "introduction": description})

            resp = await client.post(url, params=params, files=files, data=data, timeout=60)
            return resp.json()

    async def upload_news_image(self, token: str, file_path: str) -> dict:
        """上传图文正文内联图片 (返回 URL，不占永久素材额度)"""
        url = f"{WX_API_BASE}/cgi-bin/media/uploadimg"
        params = {"access_token": token}

        path = Path(file_path)
        async with httpx.AsyncClient() as client:
            files = {"media": (path.name, open(file_path, "rb"))}
            resp = await client.post(url, params=params, files=files, timeout=60)
            return resp.json()

    # ─── 草稿箱 ──────────────────────────────────────

    async def add_draft(self, token: str, articles: list[dict]) -> dict:
        """新建草稿

        articles: [{
            "title": "标题",
            "author": "作者",
            "digest": "摘要",
            "content": "HTML正文",
            "thumb_media_id": "封面图media_id",
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
            "content_source_url": ""
        }]
        """
        url = f"{WX_API_BASE}/cgi-bin/draft/add"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params, json={"articles": articles}, timeout=self.timeout
            )
            return resp.json()

    async def get_draft(self, token: str, media_id: str) -> dict:
        """获取草稿"""
        url = f"{WX_API_BASE}/cgi-bin/draft/get"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params, json={"media_id": media_id}, timeout=self.timeout
            )
            return resp.json()

    async def delete_draft(self, token: str, media_id: str) -> dict:
        """删除草稿"""
        url = f"{WX_API_BASE}/cgi-bin/draft/delete"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params, json={"media_id": media_id}, timeout=self.timeout
            )
            return resp.json()

    # ─── 发布 ────────────────────────────────────────

    async def freepublish(self, token: str, media_id: str) -> dict:
        """发布 (生成永久链接，不推送粉丝)"""
        url = f"{WX_API_BASE}/cgi-bin/freepublish/submit"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params, json={"media_id": media_id}, timeout=self.timeout
            )
            return resp.json()

    async def get_publish_status(self, token: str, publish_id: str) -> dict:
        """查询发布状态"""
        url = f"{WX_API_BASE}/cgi-bin/freepublish/get"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params, json={"publish_id": publish_id}, timeout=self.timeout
            )
            return resp.json()

    # ─── 群发 ────────────────────────────────────────

    async def mass_send_all(self, token: str, media_id: str, msg_type: str = "mpnews",
                            send_ignore_reprint: int = 0) -> dict:
        """群发 (推送所有粉丝)"""
        url = f"{WX_API_BASE}/cgi-bin/message/mass/sendall"
        params = {"access_token": token}

        payload = {
            "filter": {"is_to_all": True},
            "mpnews": {"media_id": media_id},
            "msgtype": msg_type,
            "send_ignore_reprint": send_ignore_reprint,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params, json=payload, timeout=self.timeout)
            return resp.json()

    # ─── 数据统计 ─────────────────────────────────────

    async def get_user_summary(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取用户增减数据"""
        url = f"{WX_API_BASE}/datacube/getusersummary"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()

    async def get_user_cumulate(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取累计用户数据"""
        url = f"{WX_API_BASE}/datacube/getusercumulate"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()

    async def get_article_summary(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取图文群发每日数据"""
        url = f"{WX_API_BASE}/datacube/getarticlesummary"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()

    async def get_article_total(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取图文群发总数据 (含单篇详细数据)"""
        url = f"{WX_API_BASE}/datacube/getarticletotal"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()

    async def get_user_read(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取图文统计数据"""
        url = f"{WX_API_BASE}/datacube/getuserread"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()

    async def get_user_share(self, token: str, begin_date: str, end_date: str) -> dict:
        """获取图文分享转发数据"""
        url = f"{WX_API_BASE}/datacube/getusershare"
        params = {"access_token": token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, params=params,
                json={"begin_date": begin_date, "end_date": end_date},
                timeout=self.timeout,
            )
            return resp.json()


# 全局单例
wechat_api = WeChatAPI()
