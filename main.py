import os, time, yt_dlp
import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# --- AYARLAR ---
TOKEN = os.getenv("TOKEN")
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# --- İLERLEME ÇUBUĞU ---
def progress_hook(d, status_msg):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        t = d.get('_eta_str', '---')
        try: status_msg.edit_text(f"🚀 **Onsra İşlemde...**\n\n📥 İndirme: {p}\n⏳ Kalan: {t}")
        except: pass

# --- ANA MENÜ ---
def start(update, context):
    kb = [
        [InlineKeyboardButton("🎬 Altyazı Ekle", callback_data="btn_sub"), 
         InlineKeyboardButton("🎵 Müzik İndir", callback_data="btn_dl")],
        [InlineKeyboardButton("👨‍💻 Destek", url="https://t.me/OnsraAdam")]
    ]
    update.message.reply_text(f"Selam {update.effective_user.first_name}! 🦅\nHer şey hazır. Bir işlem seç:", 
                              reply_markup=InlineKeyboardMarkup(kb))

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "btn_sub":
        query.edit_message_text("✅ **Altyazı Modu Aktif.**\n\nLütfen videoyu gönderin. (Max 5 dk)")
    elif query.data == "btn_dl":
        query.edit_message_text("✅ **Müzik Modu Aktif.**\n\nŞarkı adını veya linkini yazın.")

# --- MÜZİK/VİDEO İNDİRME ---
def handle_msg(update, context):
    text = update.message.text
    status_msg = update.message.reply_text("🔎 **YouTube Aranıyor...**")
    start_time = time.time()
    filename = f"{DOWNLOAD_DIR}/m_{int(time.time())}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename.replace('.mp3', ''),
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': 'Mozilla/5.0 (Android 14; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0',
        'progress_hooks': [lambda d: progress_hook(d, status_msg)],
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{text}", download=True)['entries'][0]
            if info.get('duration', 0) > 300:
                status_msg.edit_text("⚠️ **Hata:** 5 dakikadan uzun videolar indirilemez.")
                return

        elapsed = round(time.time() - start_time, 1)
        status_msg.edit_text(f"✅ İndirildi ({elapsed} sn). 📤 Yükleniyor...")
        with open(filename, 'rb') as f:
            update.effective_chat.send_audio(audio=f, caption=f"🎵 {info.get('title')}\n⚡ Onsra Hızlı İndirme")
        
        if os.path.exists(filename): os.remove(filename)
        status_msg.delete()
    except Exception as e:
        status_msg.edit_text("❌ Bir hata oluştu veya video bulunamadı.")

# --- ALTYAZI İŞLEME ---
def handle_video(update, context):
    status_msg = update.message.reply_text("📥 Video alınıyor...")
    ts = int(time.time())
    video_path = f"{DOWNLOAD_DIR}/v_{ts}.mp4"
    audio_path = f"{DOWNLOAD_DIR}/a_{ts}.wav"
    output_path = f"{DOWNLOAD_DIR}/onsra_{ts}.mp4"
    
    try:
        update.message.video.get_file().download(video_path)
        status_msg.edit_text("🎙 Ses analiz ediliyor...")
        
        clip = VideoFileClip(video_path)
        if clip.duration > 300:
            status_msg.edit_text("⚠️ 5 dakikadan uzun videolara altyazı eklenemez.")
            clip.close(); os.remove(video_path); return

        clip.audio.write_audiofile(audio_path, codec='pcm_s16le', verbose=False, logger=None)
        
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
            recognized_text = r.recognize_google(audio_data, language="tr-TR")

        status_msg.edit_text("🎬 Altyazı gömülüyor ve render ediliyor...")
        
        txt = TextClip(recognized_text, fontsize=24, color='white', font='Arial', 
                       bg_color='black', size=(clip.w*0.8, None), method='caption').set_duration(clip.duration).set_position(('center', 'bottom'))
        
        final = CompositeVideoClip([clip, txt])
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)

        status_msg.edit_text("📤 Gönderiliyor...")
        with open(output_path, 'rb') as f:
            update.message.reply_video(video=f, caption=f"🎬 **Altyazı İşlendi:**\n\n_{recognized_text}_")
        
        clip.close(); final.close()
        for f in [video_path, audio_path, output_path]:
            if os.path.exists(f): os.remove(f)
        status_msg.delete()
    except Exception as e:
        status_msg.edit_text("❌ Altyazı işleminde bir hata oluştu (Sessiz video olabilir).")

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(MessageHandler(Filters.video, handle_video))
    updater.start_polling(drop_pending_updates=True)
    updater.idle()
