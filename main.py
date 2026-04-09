import os, time, yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# --- AYARLAR (GitHub Secrets üzerinden gelir) ---
TOKEN = os.getenv("TOKEN")
if not os.path.exists("downloads"): os.makedirs("downloads")

# --- İLERLEME GÖSTERGESİ ---
def progress_hook(d, status_msg):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        t = d.get('_eta_str', '---')
        try:
            status_msg.edit_text(f"📥 YouTube'dan İndiriliyor: {p}\n⏳ Kalan: {t}")
        except: pass

# --- ANA KOMUTLAR ---
def start(update, context):
    user = update.effective_user.first_name
    kb = [
        [InlineKeyboardButton("🎬 Altyazı Ekle", callback_data="btn_sub"), 
         InlineKeyboardButton("🎵 Müzik İndir", callback_data="btn_dl")],
        [InlineKeyboardButton("👨‍💻 Destek", url="https://t.me/OnsraAdam")]
    ]
    update.message.reply_text(f"Selam {user}!\nLütfen yapmak istediğin işlemi seç:", reply_markup=InlineKeyboardMarkup(kb))

# --- BUTON TEPKİLERİ ---
def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    
    if data == "btn_sub":
        query.edit_message_text("✅ Altyazı Ekleme Seçildi.\n\nŞimdi bana altyazı eklememi istediğin **videoyu gönder.**")
    
    elif data == "btn_dl":
        query.edit_message_text("✅ Müzik İndirme Seçildi.\n\nŞimdi bana indirmek istediğin **şarkının adını yaz.**")
        
    elif data.startswith("dl_"):
        process_download(update, context, data)

# --- VİDEO GELİNCE ---
def handle_video(update, context):
    update.message.reply_text("🎬 Video alındı. Altyazı işleme motoru GitHub Actions üzerinde başlatılıyor...\n⚠️ Bu işlem videonun uzunluğuna göre zaman alabilir.")

def handle_msg(update, context):
    text = update.message.text
    kb = [[InlineKeyboardButton("🎵 MP3", callback_data=f"dl_mp3|{text}"), 
           InlineKeyboardButton("🎥 MP4", callback_data=f"dl_mp4|{text}")]]
    update.message.reply_text(f"🔍 '{text}' için format seçin:", reply_markup=InlineKeyboardMarkup(kb))

# --- İNDİRME FONKSİYONU ---
def process_download(update, context, data):
    query = update.callback_query
    start_time = time.time()
    mode, q_text = data.split("|")
    is_audio = "mp3" in mode
    status_msg = query.message.edit_text("⚙️ Bağlantı kuruluyor...")
    
    filename = f"downloads/f_{int(time.time())}"
    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[height<=480]+bestaudio/best',
        'outtmpl': filename + '.%(ext)s',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': 'com.google.android.youtube/19.01.35 (Linux; Android 14)',
        'progress_hooks': [lambda d: progress_hook(d, status_msg)],
    }
    
    if is_audio:
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q_text}", download=True)
            info = info['entries'][0]
            final_file = ydl.prepare_filename(info)
            if is_audio: final_file = final_file.rsplit('.', 1)[0] + ".mp3"
        
        status_msg.edit_text("📤 Yükleniyor...")
        with open(final_file, 'rb') as f:
            if is_audio: update.effective_chat.send_audio(audio=f, caption="✅ İşlem Başarılı.")
            else: update.effective_chat.send_video(video=f, caption="✅ İşlem Başarılı.")
        
        if os.path.exists(final_file): os.remove(final_file)
        status_msg.delete()
    except Exception as e:
        status_msg.edit_text("⚠️ YouTube şu an engelliyor. Lütfen SoundCloud veya başka bir isimle tekrar deneyin.")

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True, workers=32)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(MessageHandler(Filters.video, handle_video))
    updater.start_polling(drop_pending_updates=True)
    updater.idle()
  
