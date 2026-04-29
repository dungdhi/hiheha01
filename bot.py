import os, re, requests
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD_ID = os.getenv("TARGET_THREAD_ID")
TARGET_THREAD = int(THREAD_ID) if THREAD_ID and THREAD_ID.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

def get_imgs(url):
    headers = {"User-Agent":"Mozilla/5.0","Cookie":FB_COOKIE}
    for host in ["mbasic.facebook.com","m.facebook.com"]:
        u = url.replace("www.facebook.com",host).replace("facebook.com",host)
        r = requests.get(u, headers=headers, timeout=25)
        if "scontent" in r.text:
            imgs = re.findall(r"https://[^\"'\\s]+scontent[^\"'\\s]+\\.jpg", r.text)
            imgs = [i.replace("&amp;","&") for i in imgs if "profile" not in i]
            return list(dict.fromkeys(imgs))[:40]
    # nếu không thấy, trả về lý do
    raise Exception(f"FB tra ve {len(r.text)} ky tu, khong co scontent - cookie sai?")

async def h(upd,ctx):
    m = re.search(r'https?://\S*facebook\.com/\S+', upd.message.text or "")
    if not m: return
    await upd.message.reply_text("Dang lay anh...")
    try:
        imgs = get_imgs(m.group(0))
        await upd.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0,len(imgs),10):
            batch=[InputMediaPhoto(x) for x in imgs[i:i+10]]
            batch[0].caption = upd.message.text[:900]
            await ctx.bot.send_media_group(TARGET_CHAT,batch,message_thread_id=TARGET_THREAD)
    except Exception as e:
        await upd.message.reply_text(f"Loi: {e}")

app=Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start",lambda u,c:u.message.reply_text("ok")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,h))
app.run_polling()
