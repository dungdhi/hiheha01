import os, re, requests
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD_ID = os.getenv("TARGET_THREAD_ID")
TARGET_THREAD = int(THREAD_ID) if THREAD_ID and THREAD_ID.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

print(f"Bot starting - CHAT={TARGET_CHAT} THREAD={TARGET_THREAD}")

def get_fb_images(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": FB_COOKIE,
        "Accept-Language": "vi-VN,vi;q=0.9"
    }
    # dùng mbasic để nhẹ
    mbasic_url = url.replace("www.facebook.com", "mbasic.facebook.com")
    # với link share/p/ -> chuyển sang dạng xem ảnh
    if "/share/p/" in mbasic_url:
        pid = mbasic_url.split("/share/p/")[1].split("/")[0]
        mbasic_url = f"https://mbasic.facebook.com/story.php?story_fbid={pid}&id=0"
    
    r = requests.get(mbasic_url, headers=headers, timeout=25)
    r.raise_for_status()
    # tìm tất cả link ảnh scontent
    imgs = re.findall(r'https://[^"']+scontent[^"']+?\.jpg', r.text)
    # làm sạch, bỏ trùng
    clean = []
    seen = set()
    for i in imgs:
        i = i.replace("&amp;", "&").split("\")[0]
        if "profile" in i or "emoji" in i:
            continue
        if i not in seen:
            clean.append(i)
            seen.add(i)
    return clean[:40]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    m = re.search(r'https?://\S*facebook\.com/\S+', text)
    if not m:
        return
    await update.message.reply_text("Dang lay anh...")
    try:
        imgs = get_fb_images(m.group(0))
        if not imgs:
            await update.message.reply_text("Khong tim thay anh - cookie het han?")
            return
        await update.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0, len(imgs), 10):
            batch = imgs[i:i+10]
            media = [InputMediaPhoto(url) for url in batch]
            media[0].caption = text[:900]
            await context.bot.send_media_group(
                chat_id=TARGET_CHAT,
                media=media,
                message_thread_id=TARGET_THREAD
            )
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {str(e)[:200]}")
        print(f"ERROR: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB di")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_polling()
