import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters

# Web Server (To prevent Render port errors)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trenda Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# /start command handler
async def start_command(update, context):
    await update.message.reply_text("Hello! I am ready. Please send a movie or video file! 🍿")

# Media & File handler
async def handle_media(update, context):
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return

    # Generating the link
    embedUrl = f"https://t.me/c/{update.message.chat.id}/{file_id}"

    # Sending the link back to the user
    reply_text = f"✅ Your link is ready:\n\n`{embedUrl}`\n\nCopy this link and paste it into your admin panel. 👍"
    
    await update.message.reply_text(reply_text, parse_mode='Markdown')

# Main function
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    
    bot_token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
    
    print("Bot is live!")
    app.run_polling(drop_pending_updates=True)
