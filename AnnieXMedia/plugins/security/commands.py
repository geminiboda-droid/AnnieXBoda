# Authored By Certified Coders © 2026
# Security Module: Admin Commands Interface
# Logic: Dynamic Multi-Level Inline Settings & Group management

import asyncio
from pyrogram import filters, enums
from pyrogram.types import (
    Message, ChatPermissions, ChatPrivileges, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS
from config import BANNED_USERS
from .database import (
    update_lock, get_locks, set_warn_limit_db, 
    update_user_warns, get_lock_settings, set_lock_settings # تم اضافة دوال جديدة لقاعدة البيانات
)
from .helpers import has_permission, force_delete

# --- خرائط البيانات والترجمة ---
LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "all", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood",
    "الكلايش": "long_msgs", "الانلاين": "inline", "الفيديو": "videos",
    "البصمات": "voice", "السيلفي": "video_notes", "الماركدوان": "markdown",
    "التوجيه": "forward", "الاغاني": "audio", "الجهات": "contacts", 
    "الاشعارات": "service", "السب": "porn_text", "الاباحي": "porn_media"
}

PRETTY_MAP = {v: k for k, v in LOCK_MAP.items()}

# ==========================================
# أوامر الإدارة المباشرة (سماح، كتم، فك)
# ==========================================

@app.on_message(filters.regex(r"^(سماح|شد سماح|كتم|شد ميوت|فك الكتم)$") & filters.group & ~BANNED_USERS)
async def admin_cmds_handler(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): 
        return await message.reply("هذا الأمر مخصص للمشرفين فقط.")
        
    cmd = message.text
    if not message.reply_to_message:
        return await message.reply("يجب الرد على رسالة المستخدم لتنفيذ هذا الأمر.")
    
    target_user = message.reply_to_message.from_user
    u_id, mention = target_user.id, target_user.mention
    
    try:
        if cmd == "سماح":
            await app.promote_chat_member(message.chat.id, u_id, privileges=ChatPrivileges(can_manage_chat=True, can_delete_messages=True, can_restrict_members=True))
            await message.reply(f"تم منح صلاحيات الأدمن لـ {mention}")
        elif cmd == "شد سماح":
            await app.promote_chat_member(message.chat.id, u_id, privileges=ChatPrivileges(can_manage_chat=False))
            await message.reply(f"تم سحب صلاحيات الأدمن من {mention}")
        elif cmd == "كتم":
            await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False))
            await message.reply(f"تم كتم المستخدم {mention}")
        elif cmd in ["شد ميوت", "فك الكتم"]:
            await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True))
            await message.reply(f"تم فك الكتم عن {mention}")
    except Exception as e:
        await message.reply("حدث خطأ، تأكد من أن البوت مشرف ولديه الصلاحيات الكافية.")

# ==========================================
# أوامر التنظيف والتدمير (محسنة بالـ Concurrency)
# ==========================================

@app.on_message(filters.regex(r"^(مسح|تنظيف)($| )") & filters.group & ~BANNED_USERS)
async def destructive_clear(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): 
        return await message.reply("هذا الأمر مخصص للمشرفين فقط.")
        
    if message.reply_to_message:  
        start_id = message.reply_to_message.id
        end_id = message.id  
        msg_ids = list(range(start_id, end_id + 1))  
        
        # استخدام التوازي (Gather) للحذف اللحظي (ميزة Python 3+ القوية)
        chunks = [msg_ids[i:i+100] for i in range(0, len(msg_ids), 100)]
        await asyncio.gather(*[app.delete_messages(message.chat.id, chunk) for chunk in chunks], return_exceptions=True)
        deleted = len(msg_ids)  
    else:
        parts = message.text.split()
        num = int(parts[1]) if len(parts) > 1 else 100  
        deleted = await force_delete(message.chat.id, message.id, num)
    
    temp = await message.reply(f"تم مسح {deleted} رسالة بنجاح.")  
    await asyncio.sleep(3)
    await temp.delete()

# ==========================================
# نظام اللوحة التفاعلية الديناميكية (Dynamic UI)
# ==========================================

async def get_main_panel(chat_id):
    """اللوحة الرئيسية للأقفال"""
    kb = []
    # هنا نفترض أن get_lock_settings ترجع قاموس فيه إعدادات القفل لكل عنصر
    settings = await get_lock_settings(chat_id) 
    
    items = list(PRETTY_MAP.keys())
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                k = items[i + j]
                n = PRETTY_MAP[k]
                status = "🔒" if k in settings else "🔓"
                row.append(InlineKeyboardButton(f"{n} {status}", callback_data=f"sec_cfg_{k}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("إغلاق اللوحة", callback_data="close_sec")])
    return InlineKeyboardMarkup(kb)

def get_action_panel(key):
    """لوحة تحديد نوع العقوبة"""
    name = PRETTY_MAP.get(key, key)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("حظر (Ban)", callback_data=f"sec_act_{key}_b"), InlineKeyboardButton("طرد (Kick)", callback_data=f"sec_act_{key}_k")],
        [InlineKeyboardButton("كتم (Mute)", callback_data=f"sec_act_{key}_m")],
        [InlineKeyboardButton("فتح القفل", callback_data=f"sec_unl_{key}")],
        [InlineKeyboardButton("رجوع", callback_data="sec_back_main")]
    ])

def get_warn_panel(key, action):
    """لوحة تحديد عدد التحذيرات"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("بدون تحذير (مباشر)", callback_data=f"sec_wrn_{key}_{action}_0")],
        [InlineKeyboardButton("1", callback_data=f"sec_wrn_{key}_{action}_1"), InlineKeyboardButton("2", callback_data=f"sec_wrn_{key}_{action}_2"), InlineKeyboardButton("3", callback_data=f"sec_wrn_{key}_{action}_3")],
        [InlineKeyboardButton("4", callback_data=f"sec_wrn_{key}_{action}_4"), InlineKeyboardButton("5", callback_data=f"sec_wrn_{key}_{action}_5")],
        [InlineKeyboardButton("رجوع", callback_data=f"sec_cfg_{key}")]
    ])

def get_time_panel(key, action, warns, hours):
    """لوحة تحديد مدة الكتم الخاصة"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ ساعة", callback_data=f"sec_tim_{key}_{action}_{warns}_{hours+1}"),
            InlineKeyboardButton(f"{hours} ساعة", callback_data="ignore_cb"),
            InlineKeyboardButton("➖ ساعة", callback_data=f"sec_tim_{key}_{action}_{warns}_{max(1, hours-1)}")
        ],
        [InlineKeyboardButton("♾️ دائماً (أبدي)", callback_data=f"sec_sav_{key}_{action}_{warns}_0")],
        [InlineKeyboardButton("✅ حفظ الإعدادات", callback_data=f"sec_sav_{key}_{action}_{warns}_{hours}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"sec_act_{key}_{action}")]
    ])

@app.on_message(filters.regex(r"^(الاعدادات|locks)$") & filters.group & ~BANNED_USERS)
async def settings_panel(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): 
        return await message.reply("هذا الأمر مخصص للمشرفين فقط.")
    await message.reply_text(
        f"**لوحة تحكم الحماية الشاملة:**\nالمجموعة: {message.chat.title}\n\nاختر العنصر لتخصيص العقوبة (طرد، حظر، كتم) والتحذيرات:", 
        reply_markup=await get_main_panel(message.chat.id)
    )

# ==========================================
# معالج التفاعلات (Callback Handler - State Machine)
# ==========================================

@app.on_callback_query(filters.regex(r"^(sec_|close_sec|ignore_cb)"))
async def security_callback_handler(_, cb: CallbackQuery):
    if cb.data == "ignore_cb": return await cb.answer()
    
    if not await has_permission(cb.message.chat.id, cb.from_user.id): 
        return await cb.answer("هذا الأمر مخصص للمشرفين فقط.", show_alert=True)
        
    data = cb.data
    chat_id = cb.message.chat.id

    if data == "close_sec": 
        return await cb.message.delete()
        
    elif data == "sec_back_main":
        await cb.message.edit_text("**لوحة تحكم الحماية الشاملة:**", reply_markup=await get_main_panel(chat_id))

    # 1. فتح خيارات القفل لعنصر معين
    elif data.startswith("sec_cfg_"):
        key = data.split("_")[2]
        await cb.message.edit_text(f"إعدادات عقوبة ↫ **{PRETTY_MAP.get(key, key)}**\nاختر نوع العقوبة:", reply_markup=get_action_panel(key))

    # 2. فك القفل بالكامل
    elif data.startswith("sec_unl_"):
        key = data.split("_")[2]
        await set_lock_settings(chat_id, key, None) # حذف القفل من الداتا بيز
        await cb.answer(f"تم فتح {PRETTY_MAP.get(key, key)}", show_alert=True)
        await cb.message.edit_reply_markup(reply_markup=await get_main_panel(chat_id))

    # 3. اختيار العقوبة (بفتح التحذيرات)
    elif data.startswith("sec_act_"):
        _, _, key, action = data.split("_")
        await cb.message.edit_text(f"حدد عدد التحذيرات المسموح بها قبل العقوبة لـ **{PRETTY_MAP.get(key, key)}**:", reply_markup=get_warn_panel(key, action))

    # 4. اختيار التحذيرات (إذا كتم -> وقت، وإذا غيره -> حفظ)
    elif data.startswith("sec_wrn_"):
        _, _, key, action, warns = data.split("_")
        if action == "m": # كتم
            await cb.message.edit_text("حدد مدة الكتم:", reply_markup=get_time_panel(key, action, warns, 1))
        else:
            # حظر أو طرد (يتم الحفظ فوراً بدون وقت)
            settings = {"action": action, "warns": int(warns), "time": 0}
            await set_lock_settings(chat_id, key, settings)
            await cb.answer("تم حفظ الإعدادات بنجاح!", show_alert=True)
            await cb.message.edit_text("**لوحة تحكم الحماية الشاملة:**", reply_markup=await get_main_panel(chat_id))

    # 5. تعديل وقت الكتم
    elif data.startswith("sec_tim_"):
        _, _, key, action, warns, hours = data.split("_")
        await cb.message.edit_reply_markup(reply_markup=get_time_panel(key, action, warns, int(hours)))

    # 6. الحفظ النهائي (للكتم)
    elif data.startswith("sec_sav_"):
        _, _, key, action, warns, hours = data.split("_")
        settings = {"action": action, "warns": int(warns), "time": int(hours)}
        await set_lock_settings(chat_id, key, settings)
        await cb.answer("تم حفظ إعدادات الكتم بنجاح!", show_alert=True)
        await cb.message.edit_text("**لوحة تحكم الحماية الشاملة:**", reply_markup=await get_main_panel(chat_id))

@app.on_callback_query(filters.regex(r"^u_unmute_"))
async def unmute_inline_callback(_, cb: CallbackQuery):
    if not await has_permission(cb.message.chat.id, cb.from_user.id): 
        return await cb.answer("هذا الأمر مخصص للمشرفين فقط.", show_alert=True)
    u_id = int(cb.data.split("_")[2])  
    try:
        await app.restrict_chat_member(cb.message.chat.id, u_id, ChatPermissions(can_send_messages=True))  
        await cb.message.edit("تم فك الكتم عن المستخدم بنجاح.")
    except: 
        await cb.answer("حدث خطأ أثناء فك الكتم.", show_alert=True)
