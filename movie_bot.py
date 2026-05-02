import os
import logging
from datetime import time
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_KEY", "")
CHANNEL_ID     = os.getenv("CHANNEL_ID", "")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def ask_claude(prompt):
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
        system="أنت خبير سينمائي. عند اقتراح فيلم أعطِ: الاسم، السنة، التقييم، القصة باختصار، ولماذا يستحق المشاهدة. استخدم إيموجي واكتب بالعربية.",
    )
    return msg.content[0].text

async def cmd_start(update, ctx):
    await update.message.reply_text("🎬 *بوت اقتراح الأفلام*\n\n/movie – فيلم عشوائي\n/genre رعب – حسب النوع\n/top – أفضل 3 أفلام\n/publish – نشر في القناة", parse_mode="Markdown")

async def cmd_movie(update, ctx):
    await update.message.reply_text("⏳ جاري البحث...")
    await update.message.reply_text(ask_claude("اقترح فيلماً مميزاً يستحق المشاهدة."))

async def cmd_genre(update, ctx):
    args = " ".join(ctx.args).strip()
    if not args:
        await update.message.reply_text("اكتب النوع مثلاً: /genre كوميدي")
        return
    await update.message.reply_text(f"⏳ أبحث عن فيلم {args}...")
    await update.message.reply_text(ask_claude(f"اقترح فيلماً من نوع '{args}'."))

async def cmd_top(update, ctx):
    await update.message.reply_text("⏳ جاري التجميع...")
    await update.message.reply_text(ask_claude("اقترح أفضل 3 أفلام من أنواع مختلفة."))

async def cmd_publish(update, ctx):
    text = ask_claude("اقترح فيلم اليوم لقناة تيليغرام. ابدأ بـ 🎬 فيلم اليوم")
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=text)
    await update.message.reply_text("✅ تم النشر!")

async def daily_post(ctx):
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=ask_claude("اقترح فيلم اليوم. ابدأ بـ 🎬 فيلم اليوم"))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("movie", cmd_movie))
    app.add_handler(CommandHandler("genre", cmd_genre))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.job_queue.run_daily(daily_post, time=time(hour=18, minute=0))
    log.info("🤖 البوت يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
