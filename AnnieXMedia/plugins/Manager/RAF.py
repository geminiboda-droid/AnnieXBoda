# Authored By Certified Coders 2026
# Module: Admin Promotions (Arabic + No Emojis)
# Fixed: No More "unhashable type: 'user'" Error

import asyncio
import re
from typing import Optional

from pyrogram import filters, enums
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid
from pyrogram.types import ChatAdministratorRights, Message

from AnnieXMedia import app
from AnnieXMedia.utils.decorator import admin_required
from AnnieXMedia.utils.permissions import extract_user_and_title, mention, parse_time


# ────────────────────────────────────────────────────────────
# صلاحيات المشرفين (Privilege presets)
# ────────────────────────────────────────────────────────────

_LIMITED_PRIVS = ChatAdministratorRights(
    can_change_info=False,
    can_delete_messages=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_restrict_members=False,
    can_promote_members=False,
    can_manage_chat=True,
    can_manage_video_chats=True,
    is_anonymous=False,
)

_FULL_PRIVS = ChatAdministratorRights(
    can_manage_chat=True,
    can_change_info=True,
    can_delete_messages=True,
    can_invite_users=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_promote_members=True,
    can_manage_video_chats=True,
    is_anonymous=False,
)

_DEMOTE_PRIVS = ChatAdministratorRights(
    can_change_info=False,
    can_delete_messages=False,
    can_invite_users=False,
    can_pin_messages=False,
    can_restrict_members=False,
    can_promote_members=False,
    can_manage_chat=False,
    can_manage_video_chats=False,
    is_anonymous=False,
)

# ────────────────────────────────────────────────────────────
# نصوص الاستخدام (Usage strings)
# ────────────────────────────────────────────────────────────
_USAGES = {
    "promote":     "طريقة الاستخدام: رفع @يوزر [لقب] - أو بالرد على رسالة العضو بكلمة رفع [لقب]",
    "fullpromote": "طريقة الاستخدام: رفع كامل @يوزر [لقب] - أو بالرد بكلمة رفع كامل [لقب]",
    "demote":      "طريقة الاستخدام: تنزيل @يوزر - أو بالرد بكلمة تنزيل",
    "tempadmin":   "طريقة الاستخدام: رفع مؤقت @يوزر <المدة> - أو بالرد بكلمة رفع مؤقت <المدة>",
}

def _usage(cmd: str) -> str:
    return _USAGES.get(cmd, "طريقة الاستخدام خاطئة.")

async def _info(msg: Message, text: str):
    await msg.reply_text(text)

def _format_success(action: str, chat: Message, uid: int, name: str, title: Optional[str] = None) -> str:
    chat_name = chat.chat.title
    # إجبار اليوزر أيدي يكون رقم صحيح (int) لمنع خطأ unhashable
    try:
        u_id = int(uid)
        a_id = int(chat.from_user.id)
    except:
        u_id = uid
        a_id = chat.from_user.id

    user_m    = mention(u_id, name)
    admin_m   = mention(a_id, chat.from_user.first_name)
    text = (
        f"{action} في {chat_name}\n"
        f"العضو : {user_m}\n"
        f"بواسطة : {admin_m}"
    )
    if title:
        text += f"\nاللقب: {title}"
    return text

# ────────────────────────────────────────────────────────────
# أمر الرفع (عادي)
# ────────────────────────────────────────────────────────────
@app.on_message(
    filters.regex(r"^(?:[/!.]?)رفع(?:\s+(?!ادمن|جودة)(.*))?$", flags=re.IGNORECASE) & filters.group
)
@admin_required("can_promote_members")
async def promote_command(client, message: Message):
    message.command = message.text.split()
    
    if len(message.command) == 1 and not message.reply_to_message:
        return await _info(message, _usage("promote"))

    data = await extract_user_and_title(message, client)
    if not data: return
    
    # التأكد أن uid رقم وليس كائن مستخدم
    raw_uid, name, title = data
    try:
        uid = int(raw_uid.id) if hasattr(raw_uid, "id") else int(raw_uid)
    except:
        uid = raw_uid

    if not uid: return

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=_LIMITED_PRIVS,
        )
        if title:
            try:
                await client.set_administrator_title(message.chat.id, uid, title)
            except: pass
        await message.reply_text(_format_success("تم رفع مشرف", message, uid, name, title))
    except ChatAdminRequired:
        await message.reply_text("أحتاج صلاحية إضافة مشرفين.")
    except UserAdminInvalid:
        await message.reply_text("لا يمكنني رفع هذا العضو.")
    except Exception as e:
        await message.reply_text(f"خطأ: {e}")

# ────────────────────────────────────────────────────────────
# أمر الرفع الكامل
# ────────────────────────────────────────────────────────────
@app.on_message(
    filters.regex(r"^(?:[/!.]?)رفع كامل(?:\s+(.*))?$", flags=re.IGNORECASE) & filters.group
)
@admin_required("can_promote_members")
async def fullpromote_command(client, message: Message):
    message.command = message.text.split()
    if len(message.command) <= 1 and not message.reply_to_message:
        return await _info(message, _usage("fullpromote"))

    data = await extract_user_and_title(message, client)
    if not data: return
    
    raw_uid, name, title = data
    try:
        uid = int(raw_uid.id) if hasattr(raw_uid, "id") else int(raw_uid)
    except:
        uid = raw_uid

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=_FULL_PRIVS,
        )
        if title:
            try:
                await client.set_administrator_title(message.chat.id, uid, title)
            except: pass
        await message.reply_text(_format_success("تم رفع مشرف بكل الصلاحيات", message, uid, name, title))
    except ChatAdminRequired:
        await message.reply_text("أحتاج صلاحية إضافة مشرفين.")
    except UserAdminInvalid:
        await message.reply_text("لا يمكنني رفع هذا العضو.")

# ────────────────────────────────────────────────────────────
# أمر التنزيل
# ────────────────────────────────────────────────────────────
@app.on_message(
    filters.regex(r"^(?:[/!.]?)تنزيل(?:\s+(?!ادمن)(.*))?$", flags=re.IGNORECASE) & filters.group
)
@admin_required("can_promote_members")
async def demote_command(client, message: Message):
    message.command = message.text.split()
    if len(message.command) == 1 and not message.reply_to_message:
        return await _info(message, _usage("demote"))

    data = await extract_user_and_title(message, client)
    if not data: return
    
    raw_uid, name, _ = data
    try:
        uid = int(raw_uid.id) if hasattr(raw_uid, "id") else int(raw_uid)
    except:
        uid = raw_uid

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=_DEMOTE_PRIVS,
        )
        await message.reply_text(_format_success("تم تنزيل المشرف", message, uid, name))
    except ChatAdminRequired:
        await message.reply_text("أحتاج صلاحية إضافة مشرفين.")
    except UserAdminInvalid:
        await message.reply_text("لا يمكنني تنزيل هذا العضو.")

# ────────────────────────────────────────────────────────────
# أمر الرفع المؤقت
# ────────────────────────────────────────────────────────────
@app.on_message(
    filters.regex(r"^(?:[/!.]?)رفع مؤقت(?:\s+(.*))?$", flags=re.IGNORECASE) & filters.group
)
@admin_required("can_promote_members")
async def tempadmin_command(client, message: Message):
    message.command = message.text.split()
    
    if ((not message.reply_to_message and len(message.command) < 3) or
        (message.reply_to_message and len(message.command) < 2)):
        return await _info(message, _usage("tempadmin"))

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        time_arg = message.command[1]
        title = message.text.partition(time_arg)[2].strip() or None
    else:
        try:
            user = await client.get_users(message.command[1])
            time_arg = message.command[2]
            title = message.text.partition(time_arg)[2].strip() or None
        except:
            return await message.reply_text("لم يتم العثور على العضو.")

    delta = parse_time(time_arg)
    if not delta:
        return await message.reply_text("صيغة الوقت خاطئة.")

    uid = int(user.id)
    name = user.first_name

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=_FULL_PRIVS,
        )
        await message.reply_text(_format_success(f"تم رفعه مؤقتا لمدة {time_arg}", message, uid, name, title))
        
        async def _auto_demote():
            await asyncio.sleep(delta.total_seconds())
            try:
                await client.promote_chat_member(chat_id=message.chat.id, user_id=uid, privileges=_DEMOTE_PRIVS)
                await client.send_message(message.chat.id, f"انتهت مدة رفع {mention(uid, name)} وتم تنزيله.")
            except: pass

        asyncio.create_task(_auto_demote())
    except Exception as e:
        await message.reply_text(f"فشل الرفع المؤقت: {e}")
