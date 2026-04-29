import os, subprocess, json, re
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD = os.getenv("TARGET_THREAD_ID")
TARGET_THREAD = int(THREAD) if THREAD and THREAD.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

COOKIE_FILE = "/tmp/fbcookies.txt"

def write_cookie():
    with open(COOKIE_FILE, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for part in FB_COOKIE.split(";"):
            if "=" not in part: continue
            name, val = part.strip().split("=",1)
            f.write(f".facebook.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{val}\n")

def get_fb_media(url):
    write_cookie()
    cmd = ["yt-dlp", "--cookies", COOKIE_FILE, "-J", "--no-warnings", "--quiet", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if proc.returncode!= 0:
        raise Exception(proc.stderr[:200] or "yt-dlp loi")
    data = json.loads(proc.stdout)
    urls = []
    # post nhiều ảnh -> entries
    if "entries" in data and data["entries"]:
        for e in data["entries"]:
            u = e.get("url") or e.get("webpage_url")
            if u: urls.append(u)
    # post 1 ảnh/video
    elif data.get("url"):
        urls.append(data["url"])
    # fallback lấy thumbnails
    if not urls and "thumbnails" in data:
        urls = [t["url"] for t in data["thumbnails"] if "scontent" in t["url"]]
    # lọc trùng, bỏ avatar
    uniq = []
    for u in urls:
        if "scontent" in u and u not in uniq and "profile" not in u:
            uniq.append(u.split("?")[0])
    return uniq[:40]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = re.search(r"https?://\S*facebook\.com/\S+", update.message.text or "")
    if not m: return
    await update.message.reply_text("Dang lay anh...")
    try:
        imgs = get_fb_media(m.group(0))
        if not imgs:
            await update.message.reply_text("Khong lay duoc media - kiem tra cookie")
            return
        await update.message.reply_text(f"Tim thay {len(imgs)} anh/video")
        # gửi theo nhóm 10
        for i in range(0, len(imgs), 10):
            batch = imgs[i:i+10]
            media = [InputMediaPhoto(u) for u in batch if u.endswith((".jpg",".png",".webp"))]
            if not media: continue
            if i == 0: media[0].caption = update.message.text[:900]
            await context.bot.send_media_group(TARGET_CHAT, media, message_thread_id=TARGET_THREAD)
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
