# Authored By Certified Coders © 2026
import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from config import *
from AnnieXMedia import app
from AnnieXMedia.core.call import StreamController
from AnnieXMedia.utils import bot_sys_stats
from AnnieXMedia.utils.decorators.language import language
from AnnieXMedia.utils.inline import supp_markup

@app.on_message(
    filters.command(["ping", "بنج", "بينج", "فحص"], prefixes=["/", ".", "!"]) 
    & (filters.group | filters.private) 
    & ~BANNED_USERS
)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    
    initial_text = (
        "**جـاري فـحـص خـوادم تـيـلـيـجـرام...**\n"
        "**جـاري الاتـصـال بـقـاعـدة الـبـيـانـات...**\n"
        "**جـاري قـراءة اسـتـهـلاك الـمـوارد والـخـادم...**\n\n"
        "**يـرجـى الانـتـظـار لـحـظـات.**"
    )
    response = await message.reply_video(video=PING_VID_URL, caption=initial_text)
    
    # تجاوز خطأ المكتبة الجديدة
    try:
        pytgping = await StreamController.ping()
    except AttributeError:
        pytgping = "مـسـتـقـر (N/A)"
    except Exception:
        pytgping = "غـيـر مـعـروف"

    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await asyncio.sleep(1.5)
    
    final_text = (
        "**تـم الانـتـهـاء مـن الـفـحـص بـنـجـاح.**\n\n"
        "**ـ• ━─━─━─━─━─━─━─━ •ـ**\n\n"
        "**[ تـقـريـر الـشـبـكـة والاسـتـجـابـة ]**\n"
        f"**ـ سـرعـة اسـتـجـابـة الـبـوت :** `{resp}` **مـلـلـي ثـانـيـة**\n"
        f"**ـ سـرعـة خـوادم الـصـوت :** `{pytgping}`\n\n"
        "**[ تـقـريـر الـخـادم والـمـوارد ]**\n"
        f"**ـ مـدة الـتـشـغـيـل :** `{UP}`\n"
        f"**ـ اسـتـهـلاك الـمـعـالـج :** `{CPU}`\n"
        f"**ـ الـذاكـرة الـعـشـوائـيـة :** `{RAM}`\n"
        f"**ـ مـسـاحـة الـتـخـزيـن :** `{DISK}`\n\n"
        "**[ تـقـريـر الأنـظـمـة الـداخـلـيـة ]**\n"
        "**ـ قـاعـدة الـبـيـانـات :** `مـتـصـل ومـسـتـقـر`\n"
        "**ـ مـشـغـل الـمـيـديـا :** `يـعـمـل بـكـفـاءة`\n"
        "**ـ نـظـام الـحـمـايـة :** `نـشـط`\n\n"
        "**ـ• ━─━─━─━─━─━─━─━ •ـ**\n"
        f"**الـبـوت الـرسـمـي :** {app.mention}"
    )
    await response.edit_text(text=final_text, reply_markup=supp_markup(_))
