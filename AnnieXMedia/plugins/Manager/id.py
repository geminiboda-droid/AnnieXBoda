# Authored By Certified Coders © 2026
import re
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from AnnieXMedia import app

@app.on_message(filters.regex(r"^(id|ا|ايدي|الايدي)$", flags=re.IGNORECASE))
async def get_id_custom(client, message: Message):
    chat = message.chat
    
    # 1. تحديد الشخص المستهدف (لو عامل ريبلاي هيجيب بيانات التاني، لو مفيش هيجيب بياناتك)
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user

    if not target_user:
        return await message.reply_text("**تعذر العثور على بيانات المستخدم.**")

    # 2. سحب البايو (يحتاج فحص عميق للحساب)
    try:
        full_user = await client.get_chat(target_user.id)
        bio = full_user.bio or "لا يوجد بايو"
    except Exception:
        bio = "لا يوجد بايو"

    # 3. تظبيط البيانات
    name = target_user.first_name
    if target_user.last_name:
        name += f" {target_user.last_name}"
        
    username = f"@{target_user.username}" if target_user.username else "لا يوجد"
    user_id = target_user.id
    chat_name = chat.title if chat.title else "محادثة خاصة"
    chat_id = chat.id

    # 4. تجميع النص بالشكل المطلوب
    text = (
        f"╭⎋¦ᚐ𝙽𝙰𝙼𝙴 : {name}\n"
        f"╰⊚ᚐᴜsᴇʀᚐ : {username}\n"
        f"╭⎋ɪᴅᚐ : `{user_id}`\n"
        f"╰⊚ᚐʙɪᴏᚐ : {bio}\n"
        f"♥ ¦ 𝙲𝙷𝙰𝚃 : {chat_name}\n"
        f"☘️ ¦ 𝙸𝙳.𝙶𝚁𝙾𝚄𝙿 : `{chat_id}`"
    )

    # 5. زر الانلاين للدخول للبروفايل
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("• الدخول للبروفايل •", url=f"tg://user?id={user_id}")]
    ])

    # 6. إرسال الرسالة
    await message.reply_text(
        text,
        reply_markup=markup,
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN
    )
