import os, re, asyncio
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("TARGET_CHAT_ID"))
TARGET_THREAD = int(os.getenv("TARGET_THREAD_ID")) if os.getenv("TARGET_THREAD_ID") else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

def parse_cookie(cookie_str):
    cookies = []
    for part in cookie_str.split(";"):
        if "=" in part:
            name, value = part.strip().split("=", 1)
            cookies.append({"name": name, "value": value, "domain": ".facebook.com", "path": "/"})
    return cookies

async def get_fb_images(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        if FB_COOKIE:
            await context.add_cookies(parse_cookie(FB_COOKIE))
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        # click "See more" if exists
        for _ in range(3):
            try:
                await page.click("text=Xem thêm", timeout=2000)
            except:
                break
        # collect images
        imgs = await page.eval_on_selector_all("img[src*='scontent']", "els => els.map(e => e.src.split('?')[0])")
        # filter
        imgs = [i for i in imgs if "fbcdn.net" in i and "emoji" not in i and "profile" not in i]
        # dedupe keep order
        seen = set(); out = []
        for i in imgs:
            if i not in seen:
                out.append(i); seen.add(i)
        await browser.close()
        return out[:50]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = re.search(r'https?://\S+facebook\.com/\S+', update.message.text or '')
    if not m:
        return
    await update.message.reply_text("Dang lay anh, cho 30s...")
    try:
        images = await get_fb_images(m.group(0))
        if not images:
            await update.message.reply_text("Khong tim thay anh - kiem tra cookie")
            return
        await update.message.reply_text(f"Tim thay {len(images)} anh")
        for i in range(0, len(images), 10):
            batch = images[i:i+10]
            media = [{"type": "photo", "media": u} for u in batch]
            if i == 0:
                media[0]["caption"] = update.message.text[:900]
            await context.bot.send_media_group(chat_id=TARGET_CHAT, message_thread_id=TARGET_THREAD, media=media)
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_polling()
