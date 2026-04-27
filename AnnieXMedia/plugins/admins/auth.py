# Authored By Certified Coders 2026
# Module: Auth Users (Bot Admins) - Arabic & No Emojis
# Optimized for Python 3.13 & Strict Command Matching

import re
from pyrogram import filters
from pyrogram.types import Message

from AnnieXMedia import app
from AnnieXMedia.utils import extract_user, int_to_alpha
from AnnieXMedia.utils.database import (
    delete_authuser,
    get_authuser,
    get_authuser_names,
    save_authuser,
)
from AnnieXMedia.utils.decorators import AdminActual, language
from AnnieXMedia.utils.inline import close_markup
from config import BANNED_USERS, adminlist

# --- [ فلاتر صارمة لمنع التداخل مع أوامر مثل "رفع جودة" ] ---
AUTH_REGEX = r"^(?:[/!.]?)رفع ادمن(?:\s+(.*))?$"
UNAUTH_REGEX = r"^(?:[/!.]?)تنزيل ادمن(?:\s+(.*))?$"
AUTHLIST_REGEX = r"^(?:[/!.]?)الادمنية$"


# --- [ أمر رفع أدمن في البوت ] ---
@app.on_message(
    (filters.regex(AUTH_REGEX, flags=re.IGNORECASE) | filters.command("auth", prefixes=["/", "!", "."]))
    & filters.group 
    & ~BANNED_USERS
)
@AdminActual
async def auth(client, message: Message, _):
    # ضبط مدخلات الرسالة لتفادي أخطاء الصلاحيات مع extract_user
    if not message.reply_to_message:
        target_user = None
        if message.matches and message.matches[0].group(1):
            target_user = message.matches[0].group(1).strip()
        elif len(message.command) > 1:
            target_user = message.command[1]
            
        if not target_user:
            return await message.reply_text("**يرجى الرد على العضو أو كتابة المعرف لرفعه.**")
            
        # إعادة تهيئة مسار الأمر لضمان عدم حدوث أخطاء استخراج
        message.command = ["auth", target_user]
    
    user = await extract_user(message)
    if not user:
        return await message.reply_text("**تعذر العثور على هذا المستخدم.**")

    token = await int_to_alpha(user.id)
    _check = await get_authuser_names(message.chat.id)
    count = len(_check)
    
    if int(count) >= 25:
        return await message.reply_text("**لا يمكن رفع المزيد، تم الوصول للحد الأقصى (25 أدمن).**")
    
    if token not in _check:
        assis = {
            "auth_user_id": user.id,
            "auth_name": user.first_name,
            "admin_id": message.from_user.id,
            "admin_name": message.from_user.first_name,
        }
        get = adminlist.get(message.chat.id)
        if get:
            if user.id not in get:
                get.append(user.id)
        await save_authuser(message.chat.id, token, assis)
        return await message.reply_text(f"**تم رفع {user.mention} أدمن في البوت بنجاح.**")
    else:
        return await message.reply_text(f"**{user.mention} أدمن في البوت بالفعل.**")


# --- [ أمر تنزيل أدمن من البوت ] ---
@app.on_message(
    (filters.regex(UNAUTH_REGEX, flags=re.IGNORECASE) | filters.command("unauth", prefixes=["/", "!", "."]))
    & filters.group 
    & ~BANNED_USERS
)
@AdminActual
async def unauthusers(client, message: Message, _):
    if not message.reply_to_message:
        target_user = None
        if message.matches and message.matches[0].group(1):
            target_user = message.matches[0].group(1).strip()
        elif len(message.command) > 1:
            target_user = message.command[1]
            
        if not target_user:
            return await message.reply_text("**يرجى الرد على العضو أو كتابة المعرف لتنزيله.**")
            
        message.command = ["unauth", target_user]
    
    user = await extract_user(message)
    if not user:
        return await message.reply_text("**تعذر العثور على هذا المستخدم.**")

    token = await int_to_alpha(user.id)
    deleted = await delete_authuser(message.chat.id, token)
    
    get = adminlist.get(message.chat.id)
    if get:
        if user.id in get:
            get.remove(user.id)
            
    if deleted:
        return await message.reply_text(f"**تم تنزيل {user.mention} من صلاحيات البوت.**")
    else:
        return await message.reply_text(f"**{user.mention} ليس أدمن في البوت أصلاً.**")


# --- [ أمر عرض قائمة الادمنية ] ---
@app.on_message(
    (filters.regex(AUTHLIST_REGEX, flags=re.IGNORECASE) | filters.command(["authlist", "authusers"], prefixes=["/", "!", "."]))
    & filters.group 
    & ~BANNED_USERS
)
@language
async def authusers_list(client, message: Message, _):
    _wtf = await get_authuser_names(message.chat.id)
    if not _wtf:
        return await message.reply_text("**لا يوجد أدمنية مرفوعين في هذا الجروب.**")
    else:
        j = 0
        mystic = await message.reply_text("**جاري جلب القائمة...**")
        text = f"**قائمة أدمنية البوت في {message.chat.title}:**\n\n"
        for umm in _wtf:
            _umm = await get_authuser(message.chat.id, umm)
            user_id = _umm["auth_user_id"]
            admin_id = _umm["admin_id"]
            admin_name = _umm["admin_name"]
            try:
                user = (await app.get_users(user_id)).first_name
                j += 1
            except:
                continue
            text += f"{j}- {user} [`{user_id}`]\n"
            text += f"   بواسطة: {admin_name} [`{admin_id}`]\n\n"
        
        await mystic.edit_text(text, reply_markup=close_markup(_))
