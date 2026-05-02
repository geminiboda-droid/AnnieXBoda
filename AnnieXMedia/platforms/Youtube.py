import asyncio
import re
import logging
import os
import time
from contextlib import suppress
from typing import Any, Tuple, Dict, List

import aiohttp
import aiofiles
from pyrogram import enums
from yt_dlp import YoutubeDL
from youtubesearchpython.aio import VideosSearch

log = logging.getLogger("AnnieXMedia.YouTube")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        # الإعدادات الصاروخية اللي إنت اعتمدتها
        self.base_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
            "force_ipv4": True,
            "source_address": "0.0.0.0",
            "extractor_args": {
                "youtube": {
                    "client": ["android_vr"] 
                }
            }
        }

    async def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def _extract_native(self, query: str, opts: dict) -> dict:
        """دالة الاستخراج الخام باستخدام Treads عشان السرعة"""
        def extract():
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(query, download=False)
        return await asyncio.to_thread(extract)

    async def details(self, link: str, videoid: str | bool | None = None) -> tuple[str, str | None, int, str, str]:
        """سحب تفاصيل الفيديو في خبطة واحدة مع الرابط المباشر لو أمكن"""
        # بنحاول نجيب البيانات بـ yt-dlp مباشرة لأنها أدق وأسرع في سحب كل شيء معاً
        opts = self.base_opts.copy()
        try:
            info = await self._extract_native(link, opts)
            title = info.get("title", "Unknown")
            duration_sec = info.get("duration", 0)
            thumbnail = info.get("thumbnail", "")
            vid_id = info.get("id", "")
            
            # تحويل الثواني لشكل 00:00
            duration_min = time.strftime('%M:%S', time.gmtime(duration_sec))
            
            return title, duration_min, duration_sec, thumbnail, vid_id
        except Exception as e:
            log.error(f"Details extraction error: {e}")
            # Fallback لو فشل الـ yt-dlp نستخدم البحث السريع
            return "Unknown", "0:00", 0, "", ""

    async def get_direct_link(self, link: str, video: bool = False) -> str | None:
        """أسرع دالة لجلب الرابط المباشر للتشغيل"""
        opts = self.base_opts.copy()
        if video:
            opts["format"] = "bestvideo+bestaudio/best"
            
        try:
            info = await self._extract_native(link, opts)
            return info.get("url")
        except Exception as e:
            log.error(f"Direct link error: {e}")
            return None

    async def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """البحث عن فيديوهات (لأمر البحث فقط)"""
        try:
            search_obj = VideosSearch(query, limit=limit)
            result = await search_obj.next()
            if not result or "result" not in result:
                return []
            return [
                {
                    "title": d.get("title", "Unknown"), 
                    "vidid": d.get("id"), 
                    "duration": d.get("duration", "0:00")
                }
                for d in result["result"]
            ]
        except Exception as e:
            log.error(f"Search error: {e}")
            return []

    async def download_thumb(self, thumbnail_url: str) -> str | None:
        """تحميل صورة الفيديو لعرضها في المكالمة"""
        if not thumbnail_url:
            return None
        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/thumb_{int(time.time())}.jpg"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail_url) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(path, "wb") as f:
                            await f.write(await resp.read())
                        return path
        except Exception:
            return None
        return None

    async def get_playlist(self, url: str) -> list[str]:
        """سحب روابط قائمة تشغيل كاملة"""
        opts = {"extract_flat": True, "quiet": True, "skip_download": True}
        try:
            info = await self._extract_native(url, opts)
            return [f"https://www.youtube.com/watch?v={e['id']}" for e in info.get("entries", []) if e.get("id")]
        except Exception as e:
            log.error(f"Playlist error: {e}")
            return []

YouTube = YouTubeAPI()
