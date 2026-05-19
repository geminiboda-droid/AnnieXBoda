# Authored By Certified Coders © 2026
# Security Module: Main Protection Engine
# Logic: Real-time traffic analysis, Dynamic Penalties, & Content Filtering

import asyncio
import re
import time
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from fuzzywuzzy import fuzz

from AnnieXMedia import app
from .database import get_lock_settings, get_current_warns, update_user_warns
from .helpers import has_permission, scan_video_frames, check_porn_api

# --- مخازن البيانات المؤقتة لسرعة المعالجة ---
flood_cache = {} 
processed_cache = {}
BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسمك", "زب", "فحل", "بورن", "متناك", "مص", "كس", "طيز", "قحبه", "فاجره", "احاا", "متناكه", "خول"]

async def execute_penalty(message: Message, lock_key: str, settings: dict, is_religious=False):
    """تنفيذ العقوبات الديناميكي بناءً على إعدادات المشرف"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    mention = message.from_user.mention
    
    # الإعدادات المخصصة
    action = settings.get("action", "m") # m: كتم, b: حظر, k: طرد
    max_warns = settings.get("warns", 0)
    mute_hours = settings.get("time", 0)
    
    # تجاوز الإعدادات في حال كانت إساءة أخلاقية صارمة
    if is_religious:
        action, max_warns, mute_hours = "m", 3, 168 # كتم لمدة أسبوع بعد 3 تحذيرات
        
    current_warns = await get_current_warns(chat_id, user_id)
    
    # حذف الرسالة المخالفة
    try: await message.delete()
    except: pass
    
    # تنفيذ العقوبة إذا تجاوز التحذيرات
    if max_warns == 0 or current_warns >= max_warns:
        await update_user_warns(chat_id, user_id, 0)
        
        try:
            if action == "b": # حظر
                await app.ban_chat_member(chat_id, user_id)
                await message.reply(f"تم حظر المستخدم {mention} لتجاوزه قوانين المجموعة.")
                
            elif action == "k": # طرد
                await app.ban_chat_member(chat_id, user_id)
                await asyncio.sleep(1)
                await app.unban_chat_member(chat_id, user_id)
                await message.reply(f"تم طرد المستخدم {mention} لمخالفته القوانين.")
                
            elif action == "m": # كتم
                until = datetime.now() + timedelta(hours=mute_hours) if mute_hours > 0 else None
                time_text = f"لمدة {mute_hours} ساعة" if mute_hours > 0 else "نهائياً"
                if is_religious: time_text = "لمدة 7 أيام بسبب إساءة أخلاقية"
                    
                await app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
                await message.reply(f"تم كتم المستخدم {mention} {time_text} لتجاوز التحذيرات المسموح بها.")
        except:
            pass
            
    else:
        # إضافة تحذير جديد
        current_warns += 1
        await update_user_warns(chat_id, user_id, current_warns)
        reason_text = "تمت مخالفة القوانين."
        if is_religious: reason_text = "يرجى الالتزام بالأدب في الحديث."
        
        await message.reply(f"{reason_text}\nتحذير: ({current_warns}/{max_warns})")

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine_handler(_, message: Message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else 0
        
        # 1. منع تكرار المعالجة
        if chat_id not in processed_cache: processed_cache[chat_id] = []
        if message.id in processed_cache[chat_id]: return 
        processed_cache[chat_id].append(message.id)
        if len(processed_cache[chat_id]) > 100: processed_cache[chat_id].pop(0)

        # 2. استثناء المطورين والادمنية
        if user_id and await has_permission(chat_id, user_id): return
        
        # 3. جلب حالة الأقفال
        active_locks = await get_lock_settings(chat_id)
        if not active_locks: return

        # --- أ. نظام قفل الشات الشامل ---
        if "all" in active_locks:  
            try: await message.delete()  
            except: pass  
            return  

        # --- ب. محرك كاشف التكرار ---
        if "flood" in active_locks:
            now = time.time()
            flood_key = f"{chat_id}:{user_id}"
            user_history = flood_cache.get(flood_key, [])
            user_history = [t for t in user_history if now - t < 5] 
            user_history.append(now)
            flood_cache[flood_key] = user_history
            if len(user_history) > 5:
                flood_cache[flood_key] = [] 
                return await execute_penalty(message, "flood", active_locks["flood"])

        # --- ج. معالجة رسائل النظام ---
        if message.service:
            if "service" in active_locks: 
                try: await message.delete()
                except: pass
            if message.new_chat_members and "bots" in active_locks:
                for member in message.new_chat_members:
                    if member.is_bot:
                        try: 
                            await app.ban_chat_member(chat_id, member.id)
                            await message.delete()
                        except: pass
            return

        # --- د. معالجة النصوص ---
        message_text = message.text or message.caption or ""
        violated_key = None
        is_religious = False
        
        if message_text:
            if "porn_text" in active_locks: 
                clean_text = re.sub(r"[^\u0621-\u064A\s]", "", message_text)
                for word in clean_text.split():
                    if any(fuzz.ratio(bad, word) > 85 for bad in BAD_WORDS):
                        violated_key, is_religious = "porn_text", True
                        break
            
            if not violated_key:
                if "links" in active_locks and any(x in message_text for x in ["http", ".com", ".net", "t.me", "www"]): violated_key = "links"
                elif "usernames" in active_locks and "@" in message_text: violated_key = "usernames"
                elif "hashtags" in active_locks and "#" in message_text: violated_key = "hashtags"
                elif "markdown" in active_locks and any(x in message_text for x in ["**", "__", "`"]): violated_key = "markdown"
                elif "slashes" in active_locks and message_text.startswith("/"): violated_key = "slashes"
                elif "long_msgs" in active_locks and len(message_text) > 800: violated_key = "long_msgs"

        # --- هـ. معالجة الوسائط ---
        if not violated_key:
            if "photos" in active_locks and message.photo: violated_key = "photos"
            elif "videos" in active_locks and message.video: violated_key = "videos"
            elif "animations" in active_locks and message.animation: violated_key = "animations"
            elif "stickers" in active_locks and message.sticker: violated_key = "stickers"
            elif "docs" in active_locks and message.document: violated_key = "docs"
            elif "voice" in active_locks and (message.voice or message.audio): violated_key = "voice"
            elif "video_notes" in active_locks and message.video_note: violated_key = "video_notes"
            elif "contacts" in active_locks and message.contact: violated_key = "contacts"
            elif "inline" in active_locks and message.via_bot: violated_key = "inline"
            elif "forward" in active_locks and (message.forward_date or message.forward_from): violated_key = "forward"

        if violated_key:
            return await execute_penalty(message, violated_key, active_locks[violated_key], is_religious)

    except Exception as e:
        print(f"Engine Error: {e}")
