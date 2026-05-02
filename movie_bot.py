import os
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

def youtube_link(movie_name):
    query = quote(f"{movie_name} trailer مترجم")
    return f"https://www.youtube.com/results?search_query={query}"

def ask_claude(prompt):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        system="أنت خبير سينمائي. اقترح فيلماً بشكل مختصر: الاسم بالعربي والإنجليزي، السنة، التقييم، وسبب المشاهدة في سطرين. في آخر ردك اكتب فقط: MOVIE_NAME: ثم اسم الفيلم بالإنجليزي.",
    )
    return msg.content[0].text

def format_reply(raw):
    lines = raw.strip().split("\n")
    movie_name = ""
    clean_lines = []
    for line in lines:
        if line.startswith("MOVIE_NAME:"):
            movie_name = line.replace("MOVIE_NAME:", "").strip()
        else:
            clean_lines.append(line)
    text = "\n".join(clean_lines).strip()
    if movie_name:
        text += f"\n\n🎬 تريلر مترجم: {youtube_link(movie_name)}"
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
