import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web

# റെണ്ടറിൽ നിന്ന് ഡാറ്റ എടുക്കുന്നു
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://trenda-movie-bot.onrender.com")

# അഡ്വാൻസ്ഡ് Pyrogram ബോട്ട് സെറ്റപ്പ്
bot = Client("trenda_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! I am ready. Send me a movie! 🍿")

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    # ഡയറക്റ്റ് സ്ട്രീം ലിങ്ക് ഉണ്ടാക്കുന്നു
    msg_id = message.id
    link = f"{URL}/stream/{msg_id}"
    await message.reply_text(f"✅ Your Direct Stream Link:\n\n`{link}`\n\nPaste this in your admin panel!")

# സ്ട്രീമിംഗിന് വേണ്ടിയുള്ള വെബ് സർവർ
routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

@routes.get("/stream/{msg_id}")
async def stream(request):
    return web.Response(text="Stream Ready! (Video Player Connection Active)")

app = web.Application()
app.add_routes(routes)

async def main():
    await bot.start()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print("Bot is Live with Pyrogram!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
