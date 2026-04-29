import os, re
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import facebook_scraper as fs

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD = os.getenv("TARGET_THREAD_ID")
THREAD_ID = int(THREAD) if THREAD and THREAD.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")
COOKIE_FILE = "/tmp/fb_cookies.txt"

# ghi cookie Netscape 1 lần
with open(COOKIE_FILE, "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for part in FB_COOKIE.split(";"):
        if "=" not in part: continue
        k,v = part.strip().split("=",1)
        f.write(f".facebook.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")

def get_fb_images(url):
    # facebook-scraper chấp nhận trực tiếp pfbid/share link
    posts = list(fs.get_posts(
        post_urls=[url],
        cookies=COOKIE_FILE,
        options={"allow_extra_requests": False}
    ))
    if not posts:
        return []
    post = posts[0]
    imgs = post.get("images") or []
    if post.get("image") and post["image"] not in imgs:
        imgs = [post["image"]] + imgs
    # lọc
    clean = []
    for u in imgs:
        if "scontent" in u and "profile" not in u:
            clean.append(u.split("?")[0])
    return list(dict.fromkeys(clean))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = re.search(r"https?://\S*facebook\.com/\S+", update.message.text or "")
    if not m: return
    await update.message.reply_text("Dang lay anh...")
    try:
        imgs = get_fb_images(m.group(0))
        if not imgs:
            await update.message.reply_text("Khong lay duoc anh - cookie sai hoac bai viet rieng tu")
            return
        await update.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0, len(imgs), 10):
            batch = imgs[i:i+10]
            media = [InputMediaPhoto(u) for u in batch]
            if i == 0:
                media[0].caption = update.message.text[:900]
            await context.bot.send_media_group(CHAT_ID, media, message_thread_id=THREAD_ID)
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {str(e)[:200]}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
