import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
import firebase_admin
from firebase_admin import credentials, db

# 1. Firebase സെറ്റപ്പ്
json_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
cred_dict = json.loads(json_key)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trenda-store-default-rtdb.firebaseio.com/'
})
ref = db.reference('products')

# 2. വെബ് സർവർ (റെണ്ടർ പോർട്ട് പ്രശ്നം തീർക്കാൻ)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trenda Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# 3. /start കമാൻഡ് ഹാൻഡ്‌ലർ (പുതിയത്)
async def start_command(update, context):
    await update.message.reply_text("ഹലോ മച്ചാനെ! ഞാൻ റെഡിയാണ്. സിനിമയോ വീഡിയോയോ അയച്ചു താ! 🍿")

# 4. വീഡിയോ & ഫയൽ ഹാൻഡ്‌ലർ (അപ്ഡേറ്റ് ചെയ്തത്)
async def handle_media(update, context):
    # വീഡിയോ ആണോ അതോ ഫയൽ (MKV/MP4) ആണോ എന്ന് നോക്കുന്നു
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return

    movie_data = {
        "name": update.message.caption or "New Movie",
        "embedUrl": f"https://t.me/c/{update.message.chat.id}/{file_id}",
        "image": "https://via.placeholder.com/150"
    }
    ref.push(movie_data)
    await update.message.reply_text("സക്സസ് മച്ചാനെ! നിന്റെ സിനിമ സൈറ്റിൽ അപ്‌ഡേറ്റ് ആയി. ✅")

# 5. മെയിൻ റണ്ണിംഗ് ഫങ്ഷൻ
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    
    bot_token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    
    # Start കമാൻഡും, വീഡിയോ/ഡോക്യുമെന്റും സ്വീകരിക്കാൻ ബോട്ടിനെ പഠിപ്പിക്കുന്നു
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
    
    print("ബോട്ട് ലൈവ് ആണ്! പഴയ കണക്ഷനുകൾ കട്ട് ചെയ്യുന്നു...")
    app.run_polling(drop_pending_updates=True)
