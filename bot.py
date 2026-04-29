import os, re, io
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
THREAD = os.getenv("TARGET_THREAD_ID")
THREAD_ID = int(THREAD) if THREAD and THREAD.isdigit() else None
FB_COOKIE = os.getenv("FB_COOKIE", "")

def parse_cookies():
    cookies = {}
    for line in FB_COOKIE.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]
    if not cookies and "=" in FB_COOKIE:
        for part in FB_COOKIE.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k] = v
    return cookies

async def get_images(url):
    url = url.replace("www.facebook.com", "mbasic.facebook.com").replace("m.facebook.com", "mbasic.facebook.com")
    cookies_list = []
    for k, v in parse_cookies().items():
        cookies_list.append({"name": k, "value": v, "domain": ".facebook.com", "path": "/"})
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        if cookies_list:
            await context.add_cookies(cookies_list)
        page = await context.new_page()
        await page.goto(url, timeout=90000, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        for _ in range(3):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(800)
        imgs = await page.evaluate("""() => Array.from(document.images)
           .map(i=>i.src).filter(s=>s.includes('scontent')&&!s.includes('profile'))""")
        await browser.close()
    uniq = []
    for u in imgs:
        u = u.split("?")[0]
        if u not in uniq:
            uniq.append(u)
    return uniq

async def download_image(url, cookies):
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        r = await client.get(url, cookies=cookies, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        return r.content

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = re.search(r"https?://\S*facebook\.com/\S+", update.message.text or "")
    if not m:
        return
    await update.message.reply_text("Dang lay anh...")
    try:
        urls = await get_images(m.group(0))
        if not urls:
            await update.message.reply_text("Khong thay anh")
            return
        await update.message.reply_text(f"Tim thay {len(urls)} anh")
        cookies = parse_cookies()
        # tải trước
        files = []
        for u in urls:
            try:
                data = await download_image(u, cookies)
                files.append(io.BytesIO(data))
            except:
                pass
        for i in range(0, len(files), 10):
            batch = files[i:i+10]
            media = []
            for idx, bio in enumerate(batch):
                bio.name = f"img{idx}.jpg"
                if i == 0 and idx == 0:
                    media.append(InputMediaPhoto(media=bio, caption=update.message.text[:900]))
                else:
                    media.append(InputMediaPhoto(media=bio))
            await context.bot.send_media_group(chat_id=CHAT_ID, media=media, message_thread_id=THREAD_ID)
        await update.message.reply_text("Xong!")
    except Exception as e:
        await update.message.reply_text(f"Loi: {str(e)[:200]}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Gui link FB")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_polling()
