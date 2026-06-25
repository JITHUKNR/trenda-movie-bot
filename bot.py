import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials, db

# JSON ഫയലിന്റെ പേര് ഇവിടെ കൊടുക്കുക
cred = credentials.Certificate("നിന്റെ_ഫയലിന്റെ_പേര്.json") 
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trenda-store-default-rtdb.firebaseio.com/'
})

ref = db.reference('products')

async def handle_video(update: Update, context):
    video = update.message.video
    # വീഡിയോയുടെ ഡീറ്റെയിൽസ് ഫയർബേസിലേക്ക് പുഷ് ചെയ്യുന്നു
    new_movie = {
        "name": update.message.caption or "New Movie",
        "embedUrl": f"https://t.me/c/{update.message.chat.id}/{video.file_id}",
        "image": "https://via.placeholder.com/150"
    }
    ref.push(new_movie)
    await update.message.reply_text("സക്സസ്! ഈ സിനിമ ഇപ്പോൾ നിന്റെ സൈറ്റിൽ വന്നിട്ടുണ്ടാകും! ✅")

# നിന്റെ BOT TOKEN ഇവിടെ കൊടുക്കുക
app = ApplicationBuilder().token("നിന്റെ_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.VIDEO, handle_video))

app.run_polling()
