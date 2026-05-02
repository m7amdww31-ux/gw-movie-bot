import os
import re
import logging
from datetime import time
from urllib.parse import quote
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_KEY", "")
CHANNEL_ID     = os.getenv("CHANNEL_ID", "")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

AD = """
──────────────────
🎯 اشتركات تايقر تي في - Tiger TV 🎯
🔹 من متجر GW | أفضل منصة ترفيهية تجمع كل شيء في مكان واحد!

💰 الأسعار:
📅 شهر واحد: 29 ريال
📅 3 أشهر: 49 ريال
📅 6 أشهر: 70 ريال
📅 سنة كاملة: 99 ريال

🎥 المميزات:
✅ جميع القنوات العربية والعالمية
✅ أحدث الأفلام والمسلسلات
✅ بث مباشر للمباريات بجودة عالية
✅ قسم خاص للأنمي والكورسات
✅ دعم فني متواصل
✅ واجهة سهلة الاستخدام
✅ متوافق مع جميع الأجهزة

✨ ما لقيت فلمك أو مسلسلك المفضل؟
اطلبه مباشرة وسنضيفه لك خلال وقت قصير!

📩 اشترك الآن وادخل عالم الترفيه بلا حدود!
📱 واتساب: https://wa.me/966569261930
📸 انستا: https://www.instagram.com/gw.plus1
──────────────────
"""

def youtube_link(movie_name):
    query = quote(f"{movie_name} trailer مترجم")
    return f"https://www.youtube.com/results?search_query={query}"

def ask_claude(prompt):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=350,
        messages=[{"role": "user", "content": prompt}],
        system="أنت خبير سينمائي. اقترح فيلماً بالعربية مع إيموجي. اكتب اسم الفيلم الإنجليزي بين قوسين مربعين هكذا [Movie Name] في أول سطر.",
    )
    return msg.content[0].text

def format_reply(raw):
    match = re.search(r'\[(.+?)\]', raw)
    text = raw.strip()
    if match:
        movie_name = match.group(1)
        text += f"\n\n🎬 تريلر: {youtube_link(movie_name)}"
    text += AD
    return text

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *بوت اقتراح الأفلام*\n\n"
        "/movie – فيلم عشوائي\n"
        "/genre رعب – حسب النوع\n"
        "/top – أفضل 3 أفلام\n"
        "/publish – نشر في القناة",
        parse_mode="Markdown"
    )

async def cmd_movie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    await update.message.reply_text(format_reply(ask_claude("اقترح فيلماً مميزاً يستحق المشاهدة.")))

async def cmd_genre(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args).strip()
    if not args:
        await update.message.reply_text("اكتب النوع مثلاً: /genre كوميدي")
        return
    await update.message.reply_text("⏳ ثواني...")
    await update.message.reply_text(format_reply(ask_claude(f"اقترح فيلماً من نوع '{args}'.")))

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    await update.message.reply_text(format_reply(ask_claude("اقترح أفضل 3 أفلام من أنواع مختلفة.")))

async def cmd_publish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = format_reply(ask_claude("اقترح فيلم اليوم لقناة تيليغرام. ابدأ بـ 🎬 فيلم اليوم"))
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=text)
    await update.message.reply_text("✅ تم النشر!")

async def daily_post(ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.send_message(
        chat_id=CHANNEL_ID,
        text=format_reply(ask_claude("اقترح فيلم اليوم. ابدأ بـ 🎬 فيلم اليوم"))
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("movie",   cmd_movie))
    app.add_handler(CommandHandler("genre",   cmd_genre))
    app.add_handler(CommandHandler("top",     cmd_top))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.job_queue.run_daily(daily_post, time=time(hour=18, minute=0))
    log.info("🤖 البوت يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
