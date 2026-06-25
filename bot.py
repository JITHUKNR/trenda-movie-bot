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

# 2. റെണ്ടറിനെ പറ്റിക്കാൻ ഒരു വെബ് സർവർ (ഇത് പോർട്ട് പ്രശ്നം തീർക്കും)
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
        "embedUrl": f"https://t.me/c/{update.message.
