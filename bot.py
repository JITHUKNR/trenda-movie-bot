import asyncio

# പൈത്തൺ ആദ്യം തന്നെ ഈ മാജിക് ലൂപ്പ് സെറ്റ് ചെയ്യണം (ഇത് മുകളിൽ തന്നെ വേണം)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import re
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
    # പുതിയ ലിങ്ക് ഫോർമാറ്റ് (Skip ചെയ്യാൻ സൈസ് അറിയേണ്ടതുണ്ട്)
    link = f"{URL}/stream/{message.chat.id}/{message.id}"
    await message.reply_text(f"✅ Your Direct Stream Link:\n\n`{link}`\n\nPaste this in your admin panel!")

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

# വീഡിയോ സ്കിപ്പ് ചെയ്യാൻ സപ്പോർട്ട് നൽകുന്ന പുതിയ സ്ട്രീമിംഗ് ഭാഗം
@routes.get("/stream/{chat_id}/{msg_id}")
async def stream(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        msg_id = int(request.match_info['msg_id'])
        
        # സിനിമയുടെ സൈസ് കണ്ടുപിടിക്കാൻ
        msg = await bot.get_messages(chat_id, msg_id)
        file = msg.video or msg.document
        file_size = file.file_size
        
        # യൂസർ ഏത് മിനിറ്റിലേക്കാണോ മാറ്റിയത് ആ ഭാഗം എടുക്കാൻ (Range Header)
        range_header = request.headers.get('Range', '')
        
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
            else:
                start = 0
                end = file_size - 1
            
            length = end - start + 1
            
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(length),
                'Content-Type': 'video/mp4'
            }
            
            response = web.StreamResponse(status=206, headers=headers)
            await response.prepare(request)
            
            # വീഡിയോയുടെ ആവശ്യപ്പെടുന്ന ഭാഗത്ത് നിന്ന് മാത്രം സ്ട്രീം ചെയ്യുക
            async for chunk in bot.stream_media(msg, offset=start, limit=length):
                await response.write(chunk)
            return response
        else:
            headers = {
                'Accept-Ranges': 'bytes',
                'Content-Length': str(file_size),
                'Content-Type': 'video/mp4'
            }
            response = web.StreamResponse(status=200, headers=headers)
            await response.prepare(request)
            async for chunk in bot.stream_media(msg):
                await response.write(chunk)
            return response
            
    except Exception as e:
        print(f"Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

app = web.Application()
app.add_routes(routes)

async def main():
    await bot.start()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print("Bot is Live and Streaming Data with Seek Support!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop.run_until_complete(main())
