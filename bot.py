import os, re, requests
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT=int(os.getenv("TARGET_CHAT_ID","0"))
THREAD=int(os.getenv("TARGET_THREAD_ID")) if os.getenv("TARGET_THREAD_ID") else None
COOKIE=os.getenv("FB_COOKIE","")

def get_imgs(url):
    headers={"User-Agent":"Mozilla/5.0","Cookie":COOKIE}
    # chuyển sang mbasic để nhẹ
    url=url.replace("www.facebook.com","mbasic.facebook.com").replace("/share/p/","/story.php?story_fbid=").split("?")[0]
    r=requests.get(url,headers=headers,timeout=20)
    imgs=re.findall(r'https://[^"]+scontent[^"]+\.jpg',r.text)
    return list(dict.fromkeys([i.split("\\")[0] for i in imgs]))[:40]

async def handle(u:Update,c:ContextTypes.DEFAULT_TYPE):
    m=re.search(r'https?://\S+facebook\.com/\S+',u.message.text or'')
    if not m:return
    await u.message.reply_text("Dang lay anh...")
    try:
        imgs=get_imgs(m.group(0))
        if not imgs: raise Exception("khong thay anh")
        await u.message.reply_text(f"Tim thay {len(imgs)} anh")
        for i in range(0,len(imgs),10):
            batch=[InputMediaPhoto(x) for x in imgs[i:i+10]]
            batch[0].caption=u.message.text[:900]
            await c.bot.send_media_group(CHAT,batch,message_thread_id=THREAD)
    except Exception as e:
        await u.message.reply_text(f"Loi: {e}")

Application.builder().token(BOT_TOKEN).build().add_handler(MessageHandler(filters.TEXT,handle)).run_polling()
