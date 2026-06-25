Import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
from pyrogram import Client, filters
from aiohttp import web

# റെണ്ടറിൽ നിന്നുള്ള ഡാറ്റ
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://trenda-movie-bot.onrender.com")

bot = Client("trenda_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! I am ready. Send me a movie! 🍿")

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    # വീഡിയോയുടെ യഥാർത്ഥ File ID എടുക്കുന്നു
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        return

    link = f"{URL}/stream/{file_id}"
    await message.reply_text(f"✅ Your Direct Stream Link:\n\n`{link}`\n\nPaste this in your admin panel!")

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

# വീഡിയോ വെബ്സൈറ്റിലേക്ക് പ്ലേ ചെയ്യിപ്പിക്കുന്ന പ്രധാന ഭാഗം
@routes.get("/stream/{file_id}")
async def stream(request):
    file_id = request.match_info['file_id']
    
    # വീഡിയോ പ്ലെയറിന് മനസ്സിലാകാൻ വേണ്ടിയുള്ള ഹെഡറുകൾ
    headers = {
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes'
    }
    
    response = web.StreamResponse(headers=headers)
    await response.prepare(request)
    
    try:
        # ടെലിഗ്രാമിൽ നിന്ന് ലൈവ് ആയി ഡാറ്റ എടുത്ത് വെബ്സൈറ്റിലേക്ക് കൊടുക്കുന്നു
        async for chunk in bot.stream_media(file_id):
            await response.write(chunk)
    except Exception as e:
        print(f"Error: {e}")
        
    return response

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
