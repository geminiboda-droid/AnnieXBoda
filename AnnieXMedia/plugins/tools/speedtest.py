# Authored By Certified Coders © 2026
import asyncio
import speedtest
from pyrogram import filters, Client
from pyrogram.types import Message

from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS
from AnnieXMedia.utils.decorators.language import language


def run_speedtest() -> dict:
    """
    تنفيذ فحص السرعة. في بايثون 3.13 (Free-Threading)، 
    هذا الكود سيعمل بالتوازي الحقيقي ولن يعيق البوت.
    """
    test = speedtest.Speedtest(secure=True)
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    return test.results.dict()


@app.on_message(filters.command(["speedtest", "spt"]) & SUDOERS)
@language
async def speedtest_function(client: Client, message: Message, lang: dict) -> None:
    try:
        m: Message = await message.reply_text(lang["server_11"])
        await m.edit_text(lang["server_12"])

        # الطريقة القياسية والحديثة في بايثون 3.13+ لتشغيل الدوال المانعة (Blocking)
        result: dict = await asyncio.to_thread(run_speedtest)

        await m.edit_text(lang["server_13"])

        output: str = lang["server_15"].format(
            result["client"]["isp"],
            result["client"]["country"],
            result["server"]["name"],
            result["server"]["country"],
            result["server"]["cc"],
            result["server"]["sponsor"],
            result["server"]["latency"],
            result["ping"],
        )

        await m.edit_text(lang["server_14"])
        await message.reply_photo(photo=result["share"], caption=output)
        await m.delete()

    except Exception as e:
        # استخدام add_note (ميزة حديثة في بايثون) لإضافة سياق للخطأ في السجلات إن احتجتها
        e.add_note("Speedtest execution failed due to network or timeout issues.")
        await message.reply_text(f"❌ <b>حدث خطأ:</b>\n<code>{e}</code>")
