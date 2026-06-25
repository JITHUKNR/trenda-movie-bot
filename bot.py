import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
from pyrogram import Client, filters
from aiohttp import web

# Render-ൽ നിന്ന് ഡാറ്റ എടുക്കുന്നു
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://trenda-movie-bot.onrender.com")

bot = Client("trenda_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! Trenda Bot is ready. Send me a movie! 🍿")

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    # Chat ID-യും Message ID-യും ഉപയോഗിച്ച് ലിങ്ക് ഉണ്ടാക്കുന്നു (Seek support-ന് ഇത് വേണം)
    link = f"{URL}/stream/{message.chat.id}/{message.id}"
    await message.reply_text(f"✅ Your Direct Stream Link:\n\n`{link}`\n\nCopy this and paste it into your admin panel. 👍")

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

# വീഡിയോ സ്ട്രീമിംഗ് രീതി: ടെലിഗ്രാം ഡയറക്റ്റ് ലിങ്കിലേക്ക് റീഡയറക്റ്റ് ചെയ്യുന്നു
@routes.get("/stream/{chat_id}/{msg_id}")
async def stream(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        msg_id = int(request.match_info['msg_id'])
        
        msg = await bot.get_messages(chat_id, msg_id)
        file = msg.video or msg.document
        
        # ടെലിഗ്രാമിന്റെ നേരിട്ടുള്ള ഫയൽ ലിങ്ക് എടുക്കുന്നു
        file_url = await bot.get_file_link(file)
        
        # പ്ലെയറിലേക്ക് നേരിട്ട് ലിങ്ക് അയക്കുന്നു (ഇത് വളരെ ഫാസ്റ്റ് ആണ്)
        raise web.HTTPFound(location=file_url)
            
    except Exception as e:
        print(f"Error: {e}")
        return web.Response(status=500, text="Streaming Error!")

app = web.Application()
app.add_routes(routes)

async def main():
    await bot.start()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print("Bot is Live and Streaming Data!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop.run_until_complete(main())
