import os
import re
import logging
import threading
from datetime import time
from urllib.parse import quote
from http.server import HTTPServer, BaseHTTPRequestHandler
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

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

#أفلام #مسلسلات #أنمي #اقتراح_فيلم #فيلم_اليوم #سينما #ترفيه #GWPlus #TigerTV #اشتراكات
──────────────────
"""

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_server():
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def youtube_link(name):
    return f"https://www.youtube.com/results?search_query={quote(name + ' trailer مترجم')}"

def ask_claude(prompt):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
        system="أنت خبير سينمائي. اقترح بالعربية مع إيموجي. اكتب اسم العمل الإنجليزي بين قوسين مربعين [Name] في أول سطر.",
    )
    return msg.content[0].text

def rating_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐", callback_data="rate_1"),
        InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
        InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
        InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
        InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5"),
    ]])

def format_reply(raw):
    match = re.search(r'\[(.+?)\]', raw)
    text = raw.strip()
    if match:
        text += f"\n\n🎬 تريلر: {youtube_link(match.group(1))}"
    text += AD
    return text

async def handle_rating(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stars = query.data.split("_")[1]
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(f"شكراً على تقييمك {'⭐' * int(stars)} 🙏")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *بوت اقتراح الأفلام والمسلسلات*\n\n"
        "/movie – فيلم عشوائي\n"
        "/series – مسلسل عشوائي\n"
        "/anime – أنمي مميز\n"
        "/genre رعب – حسب النوع\n"
        "/mood حزين – حسب مزاجك\n"
        "/similar Inception – أعمال مشابهة\n"
        "/top – أفضل 3 أفلام\n"
        "/publish – نشر في القناة",
        parse_mode="Markdown"
    )

async def cmd_movie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude("اقترح فيلماً مميزاً يستحق المشاهدة."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_series(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude("اقترح مسلسلاً مميزاً يستحق المشاهدة."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_anime(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude("اقترح أنمي مميزاً يستحق المشاهدة."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_genre(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args).strip()
    if not args:
        await update.message.reply_text("اكتب النوع مثلاً: /genre كوميدي")
        return
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude(f"اقترح فيلماً من نوع '{args}'."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_mood(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args).strip()
    if not args:
        await update.message.reply_text("اكتب مزاجك مثلاً: /mood حزين")
        return
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude(f"اقترح فيلماً مناسباً لشخص مزاجه '{args}'."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_similar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args).strip()
    if not args:
        await update.message.reply_text("اكتب اسم الفيلم مثلاً: /similar Inception")
        return
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude(f"اقترح 3 أفلام مشابهة لفيلم '{args}'."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ثواني...")
    text = format_reply(ask_claude("اقترح أفضل 3 أفلام من أنواع مختلفة."))
    await update.message.reply_text(text, reply_markup=rating_keyboard())

async def cmd_publish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = format_reply(ask_claude("اقترح فيلم اليوم لقناة تيليغرام. ابدأ بـ 🎬 فيلم اليوم"))
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=text)
    await update.message.reply_text("✅ تم النشر!")

async def daily_post(ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.send_message(
        chat_id=CHANNEL_ID,
        text=format_reply(ask_claude("اقترح فيلم اليوم. ابدأ بـ 🎬 فيلم اليوم"))
    )

async def weekly_post(ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.send_message(
        chat_id=CHANNEL_ID,
        text=format_reply(ask_claude("اقترح أفضل 5 أفلام هذا الأسبوع. ابدأ بـ 🏆 أفضل أفلام الأسبوع"))
    )

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("movie",   cmd_movie))
    app.add_handler(CommandHandler("series",  cmd_series))
    app.add_handler(CommandHandler("anime",   cmd_anime))
    app.add_handler(CommandHandler("genre",   cmd_genre))
    app.add_handler(CommandHandler("mood",    cmd_mood))
    app.add_handler(CommandHandler("similar", cmd_similar))
    app.add_handler(CommandHandler("top",     cmd_top))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate_"))
    app.job_queue.run_daily(daily_post, time=time(hour=18, minute=0))
    app.job_queue.run_daily(weekly_post, time=time(hour=20, minute=0), days=(4,))
    log.info("🤖 البوت يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
