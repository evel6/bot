import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TRACKING_URL = os.getenv("TRACKING_URL")  # مثال: https://your-app.onrender.com/track?goto=https://t.me/YourChannel

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ للدخول إلى جريدة نبأ", url=TRACKING_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "اضغط الزر التالي للدخول إلى جريدة نبأ 👇",
        reply_markup=reply_markup
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("🤖 Bot running...")
app.run_polling()
