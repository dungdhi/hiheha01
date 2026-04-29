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
    # đổi domain đúng 1 lần
    for host in ["mbasic.facebook.com","m.facebook.com"]:
        u = re.sub(r"https://(www\.|m\.|mbasic\.)?facebook\.com", f"https://{host}", url)
        r = requests.get(u, headers=headers, timeout=25, allow_redirects=True)
        if r.status_code == 200 and "scontent" in r.text:
            imgs = re.findall(r"https://[^\"'\s]+scontent[^\"'\s]+\.jpg", r.text)
            imgs = [i.replace("&amp;","&") for i in imgs if "profile" not in i and "emoji" not in i]
            uniq = []
            [uniq.append(x) for x in imgs if x not in uniq]
            return uniq[:40]
    raise Exception("Khong tim thay scontent - cookie het han hoac bi chan IP")

async def handle(update, context):
    m = re.search(r"https?://\S*facebook\.com/\S+", update.message.text or "")
    if not m: return
    await update.message.reply_text("Dang lay anh...")
    try:
        imgs = get_imgs(m.group(0))
        await update.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0, len(imgs), 10):
            batch = [InputMediaPhoto(x) for x in imgs[i:i+10]]
            if i == 0:
                batch[0].caption = update.message.text[:900]
            await context.bot.send_media_group(TARGET_CHAT, batch, message_thread_id=TARGET_THREAD)
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
