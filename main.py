import os, time, yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Token GitHub Secrets'tan gelir
TOKEN = os.getenv("TOKEN")
if not os.path.exists("downloads"): os.makedirs("downloads")

def start(update, context):
    kb = [[InlineKeyboardButton("🎬 Altyazı", callback_data="s"), 
           InlineKeyboardButton("🎵 Müzik", callback_data="m")]]
    update.message.reply_text("Onsra Bot Aktif! Bir işlem seçin:", reply_markup=InlineKeyboardMarkup(kb))

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "s": query.edit_message_text("Lütfen videoyu gönder.")
    if query.data == "m": query.edit_message_text("Lütfen şarkı adını yaz.")

def handle_msg(update, context):
    text = update.message.text
    status_msg = update.message.reply_text("🔎 Aranıyor...")
    filename = f"downloads/f_{int(time.time())}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': 'Mozilla/5.0 (Android 14; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{text}"])
        with open(filename, 'rb') as f:
            update.effective_chat.send_audio(audio=f)
        os.remove(filename)
        status_msg.delete()
    except Exception as e:
        status_msg.edit_text(f"⚠️ Hata: {str(e)[:50]}")

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    updater.start_polling()
    updater.idle()
