import os, re
from playwright.async_api import async_playwright
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("TARGET_CHAT_ID","0"))
TARGET_THREAD = int(os.getenv("TARGET_THREAD_ID")) if os.getenv("TARGET_THREAD_ID") else None
FB_COOKIE = os.getenv("FB_COOKIE","")

def parse_cookie(s):
    return [{"name":n,"value":v,"domain":".facebook.com","path":"/"}
            for n,v in (p.split("=",1) for p in s.split(";") if "=" in p)]

async def get_imgs(url):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await b.new_context()
        if FB_COOKIE: await ctx.add_cookies(parse_cookie(FB_COOKIE))
        pg = await ctx.new_page()
        await pg.goto(url, timeout=60000)
        await pg.wait_for_timeout(5000)
        imgs = await pg.eval_on_selector_all("img[src*='scontent']", "els=>els.map(e=>e.src.split('?')[0])")
        await b.close()
        return list(dict.fromkeys([i for i in imgs if "fbcdn" in i]))[:50]

async def h(update,context):
    import re
    m=re.search(r'https?://\S+facebook\.com/\S+', update.message.text or '')
    if not m: return
    await update.message.reply_text("Dang lay anh, cho 30s...")
    imgs=await get_imgs(m.group(0))
    if not imgs:
        await update.message.reply_text("Khong tim thay anh - lay cookie moi nhe")
        return
    await update.message.reply_text(f"Tim thay {len(imgs)} anh")
    for i in range(0,len(imgs),10):
        batch=imgs[i:i+10]
        media=[InputMediaPhoto(u) for u in batch]
        media[0].caption=update.message.text[:900]
        await context.bot.send_media_group(TARGET_CHAT, media, message_thread_id=TARGET_THREAD)

app=Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start",lambda u,c:u.message.reply_text("ok")))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h))
app.run_polling()
