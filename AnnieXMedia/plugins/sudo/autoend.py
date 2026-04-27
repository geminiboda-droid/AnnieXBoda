# Authored By Certified Coders © 2026
import re
from pyrogram import filters
from pyrogram.types import Message

from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS
from AnnieXMedia.utils.database import autoend_off, autoend_on

@app.on_message(
    filters.regex(r"^(تفعيل|إفعيل|ايقاف|إيقاف|تعطيل) (الانهاء التلقائي|الإنهاء التلقائي)$", flags=re.IGNORECASE) 
    & SUDOERS
)
async def auto_end_stream_v2(_, message: Message):
    input_text = message.text.lower()
    
    if "تفعيل" in input_text:
        await autoend_on()
        await message.reply_text(
            "**تم تفعيل الإنهاء التلقائي.**\n\n**المساعد هيخرج من الكول لوحده لو مفيش حد بيسمع.**"
        )
        
    elif "ايقاف" in input_text or "إيقاف" in input_text or "تعطيل" in input_text:
        await autoend_off()
        await message.reply_text(
            "**تم إيقاف الإنهاء التلقائي.**\n\n**المساعد هيفضل موجود في الكول حتى لو مفيش حد بيسمع.**"
        )
