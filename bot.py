import asyncio

# ഈ രണ്ട് വരികൾ Pyrogram import ചെയ്യുന്നതിന് മുൻപ് തന്നെ വരണം
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
import re
from pyrogram import Client, filters
from aiohttp import web

# റെണ്ടറിൽ നിന്നുള്ള ഡാറ്റ
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://trenda-movie-bot.onrender.com")

# നിന്റെ പബ്ലിക് ചാനലിന്റെ യൂസർനെയിം
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "-1003523802289")

bot = Client("trenda_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! Trenda Bot is ready. Send me an MP4 movie (Under 2GB)! 🍿")

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    link = f"{URL}/stream/{message.chat.id}/{message.id}"
    await message.reply_text(f"✅ Your Direct Stream Link:\n\n`{link}`\n\nPaste this in your admin panel!")

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

# --- പുതിയ API: ചാനലിലെ വീഡിയോകൾ ഓട്ടോമാറ്റിക് ആയി വെബ്സൈറ്റിലേക്ക് കൊടുക്കാൻ ---
@routes.get("/api/shorts")
async def get_shorts(request):
    try:
        links = []
        # ചാനലിലെ അവസാനത്തെ 20 പോസ്റ്റുകൾ എടുക്കുന്നു
        async for msg in bot.get_chat_history(CHANNEL_USERNAME, limit=20):
            if msg.video or msg.document:
                link = f"{URL}/stream/{CHANNEL_USERNAME}/{msg.id}"
                links.append(link)
                
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        }
        return web.json_response(links, headers=headers)
    except Exception as e:
        print(f"API Error: {e}")
        return web.json_response({"error": "Failed"}, status=500, headers={"Access-Control-Allow-Origin": "*"})

# പ്ലെയറിലേക്ക് നേരിട്ട് വീഡിയോ സ്ട്രീം ചെയ്യുന്ന ഭാഗം (FIXED & UPGRADED)
@routes.get("/stream/{chat_id}/{msg_id}")
async def stream(request):
    try:
        chat_id = request.match_info['chat_id']
        if chat_id.lstrip('-').isdigit():
            chat_id = int(chat_id)
            
        msg_id = int(request.match_info['msg_id'])
        
        msg = await bot.get_messages(chat_id, msg_id)
        if not msg or not (msg.video or msg.document):
            return web.Response(status=404, text="Video not found")

        file = msg.video or msg.document
        file_size = file.file_size
        
        # ടെലിഗ്രാം പരിധി: 2GB ക്ക് മുകളിലുള്ളവ ബോട്ടിന് സ്ട്രീം ചെയ്യാൻ കഴിയില്ല!
        if file_size > 2000 * 1024 * 1024:
            return web.Response(status=403, text="Error: File size exceeds Telegram Bot's 2GB limit. Please use a smaller file.")
        
        range_header = request.headers.get('Range', '')
        
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            start = int(match.group(1)) if match else 0
            end = int(match.group(2)) if match and match.group(2) else file_size - 1
            length = end - start + 1
            
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(length),
                'Content-Type': 'video/mp4',
                'Access-Control-Allow-Origin': '*'
            }
            response = web.StreamResponse(status=206, headers=headers)
            await response.prepare(request)
            
            try:
                # കൃത്യമായ സൈസിൽ വീഡിയോ മുറിച്ച് അയക്കുന്നു
                async for chunk in bot.stream_media(file.file_id, offset=start, limit=length):
                    if not chunk:
                        break
                    if length <= 0:
                        break
                    if len(chunk) > length:
                        chunk = chunk[:length]
                        
                    await response.write(chunk)
                    length -= len(chunk)
            except Exception:
                # ആളുകൾ വീഡിയോ സ്കിപ്പ് ചെയ്യുമ്പോൾ കണക്ഷൻ കട്ട് ആകും, അത് error അടിക്കാതിരിക്കാൻ
                pass 
            return response
        else:
            headers = {
                'Accept-Ranges': 'bytes',
                'Content-Length': str(file_size),
                'Content-Type': 'video/mp4',
                'Access-Control-Allow-Origin': '*'
            }
            response = web.StreamResponse(status=200, headers=headers)
            await response.prepare(request)
            try:
                async for chunk in bot.stream_media(file.file_id):
                    await response.write(chunk)
            except Exception:
                pass
            return response
            
    except Exception as e:
        print(f"Streaming Error: {e}")
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
