# Authored By Certified Coders © 2026
# System: Queue Manager (Database Handler)
# Optimized for Python 3.13: Modern Type Hints, Suppress & to_thread

import asyncio
from contextlib import suppress

from AnnieXMedia.misc import db
from AnnieXMedia.utils.formatters import check_duration, seconds_to_min
from config import autoclean, time_to_seconds


async def put_queue(
    chat_id: int,
    original_chat_id: int,
    file: str,
    title: str,
    duration: str,
    user: str,
    vidid: str,
    user_id: int,
    stream: str,
    forceplay: bool | str | None = None,
):
    """
    Standard Queue Insert for YouTube, Telegram Files, etc.
    """
    title = title.title()
    duration_in_seconds = 0
    
    # 🚀 بايثون 3.13: استخدام suppress لتجاهل الأخطاء بصمت وبدون استهلاك للذاكرة
    with suppress(Exception):
        # Calculate duration in seconds for Seek logic later
        duration_in_seconds = time_to_seconds(duration) - 3
        
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream, # Critical for Call.py (video vs audio)
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file, # The path Call.py will read
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }
    
    # 🚀 بايثون 3.13: دالة setdefault أسرع وأنظف من if chat_id not in db
    chat_queue = db.setdefault(chat_id, [])
        
    if forceplay:
        chat_queue.insert(0, put)
    else:
        # Standard append
        chat_queue.append(put)
        
    # 🔥 تعديل احترافي: عدم إضافة الروابط أو الـ IDs لقائمة التنظيف (Autoclean)
    if isinstance(file, str) and not file.startswith(("http", "vid_", "youtube")):
        if file not in autoclean:
            autoclean.append(file)


async def put_queue_index(
    chat_id: int,
    original_chat_id: int,
    file: str,
    title: str,
    duration: str,
    user: str,
    vidid: str,
    stream: str,
    forceplay: bool | str | None = None,
):
    """
    Queue Insert for M3U8 / Live Streams / Index Links
    """
    dur = 0
    # Specific check for known IP streams or direct URLs
    if "20.212.146.162" in str(vidid):
        try:
            # 🚀 بايثون 3.13: استخدام asyncio.to_thread الحديثة والسريعة
            dur = await asyncio.to_thread(check_duration, vidid)
            duration = seconds_to_min(dur)
        except Exception:
            duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
            dur = 0
            
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
    }
    
    # 🚀 تهيئة القائمة بطريقة حديثة ومختصرة
    chat_queue = db.setdefault(chat_id, [])
        
    if forceplay:
        chat_queue.insert(0, put)
    else:
        chat_queue.append(put)
