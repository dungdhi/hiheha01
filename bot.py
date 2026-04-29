import os, re
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD = os.getenv("TARGET_THREAD_ID")
THREAD_ID = int(THREAD) if THREAD and THREAD.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

def parse_cookies():
    cookies = []
    for line in FB_COOKIE.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            cookies.append({
                "name": parts[5],
                "value": parts[6],
                "domain": ".facebook.com",
                "path": "/"
            })
    if not cookies and "=" in FB_COOKIE:
        for part in FB_COOKIE.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "domain": ".facebook.com", "path": "/"})
    return cookies

async def get_images(url):
    cookies = parse_cookies()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        if cookies:
            await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        imgs = await page.evaluate("""() => {
            return Array.from(document.images)
               .map(i => i.src)
               .filter(s => s.includes('scontent') &&!s.includes('profile'));
        }""")
        await browser.close()
    uniq = []
    for u in imgs:
        u = u.split("?")[0]
        if u not in uniq:
            uniq.append(u)
    return uniq

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = re.search(r"https?://\S*facebook\.com/\S+", update.message.text or "")
    if not m:
        return
    await update.message.reply_text("Dang lay anh...")
    try:
        imgs = await get_images(m.group(0))
        if not imgs:
            await update.message.reply_text("Khong thay anh")
            return
        await update.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0, len(imgs), 10):
            batch = imgs[i:i+10]
            media = []
            for idx, url in enumerate(batch):
                if i == 0 and idx == 0:
                    media.append(InputMediaPhoto(media=url, caption=update.message.text[:900]))
                else:
                    media.append(InputMediaPhoto(media=url))
            await context.bot.send_media_group(
                chat_id=CHAT_ID,
                media=media,
                message_thread_id=THREAD_ID
            )
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {str(e)[:200]}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_polling()
