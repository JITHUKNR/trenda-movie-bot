import os
import json
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials, db

# 1. റെണ്ടറിലെ Environment Variable-ൽ നിന്ന് JSON കീ എടുക്കുന്നു
json_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
cred_dict = json.loads(json_key)
cred = credentials.Certificate(cred_dict)

# 2. Firebase Database കണക്ട് ചെയ്യുന്നു
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trenda-store-default-rtdb.firebaseio.com/'
})
ref = db.reference('products')

# 3. വീഡിയോ ലഭിക്കുമ്പോൾ പ്രവർത്തിക്കുന്ന ഫങ്ഷൻ
async def handle_video(update, context):
    video = update.message.video
    movie_data = {
        "name": update.message.caption or "New Movie",
        "embedUrl": f"https://t.me/c/{update.message.chat.id}/{video.file_id}",
        "image": "https://via.placeholder.com/150"
    }
    ref.push(movie_data)
    await update.message.reply_text("സക്സസ്! നിന്റെ സിനിമ സൈറ്റിൽ അപ്‌ഡേറ്റ് ആയി. ✅")

# 4. ബോട്ട് റൺ ചെയ്യുന്നു
if __name__ == '__main__':
    bot_token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    print("ബോട്ട് ലൈവ് ആണ്!")
    app.run_polling()
