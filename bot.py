import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder, MessageHandler, filters
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

# 3. വീഡിയോ ഹാൻഡ്‌ലർ
async def handle_video(update, context):
    video = update.message.video
    movie_data = {
        "name": update.message.caption or "New Movie",
        "embedUrl": f"https://t.me/c/{update.message.chat.id}/{video.file_id}",
        "image": "https://via.placeholder.com/150"
    }
    ref.push(movie_data)
    await update.message.reply_text("സക്സസ്! നിന്റെ സിനിമ സൈറ്റിൽ അപ്‌ഡേറ്റ് ആയി. ✅")

# 4. മെയിൻ റണ്ണിംഗ് ഫങ്ഷൻ
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    
    bot_token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    print("ബോട്ട് ലൈവ് ആണ്!")
    app.run_polling(drop_pending_updates=True)
