import os, re, subprocess
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD = os.getenv("TARGET_THREAD_ID")
THREAD_ID = int(THREAD) if THREAD and THREAD.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")
COOKIE_PATH = "/tmp/fb.txt"

def save_cookie():
    with open(COOKIE_PATH, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for p in FB_COOKIE.split(";"):
            if "=" not in p: continue
            k,v = p.strip().split("=",1)
            f.write(f".facebook.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")

def get_images(url):
    save_cookie()
    # gallery-dl tự xử lý share/p, pfbid, album
    cmd = ["gallery-dl", "-g", "--cookies", COOKIE_PATH, "--no-skip", url]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if out.returncode!= 0:
        raise RuntimeError(out.stderr.strip()[:300] or "gallery-dl loi")
    urls = [l.strip() for l in out.stdout.splitlines() if "scontent" in l and l.startswith("http")]
    # lọc trùng, bỏ avatar
    seen = []
    for u in urls:
        u = u.split("?")[0]
        if u not in seen and "profile" not in u:
            seen.append(u)
    return seen

async def handle(u: Update, c: ContextTypes.DEFAULT_TYPE):
    m = re.search(r"https?://\S*facebook\.com/\S+", u.message.text or "")
    if not m: return
    await u.message.reply_text("Dang lay anh...")
    try:
        imgs = get_images(m.group(0))
        if not imgs:
            await u.message.reply_text("Khong lay duoc anh - kiem tra lai cookie")
            return
        await u.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0, len(imgs), 10):
            batch = imgs[i:i+10]
            media = [InputMediaPhoto(url) for url in batch]
            if i == 0: media[0].caption = u.message.text[:900]
            await c.bot.send_media_group(CHAT_ID, media, message_thread_id=THREAD_ID)
        await u.message.reply_text("Xong!")
    except Exception as e:
        await u.message.reply_text(f"Loi: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda x,y: x.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
