import asyncio

# ഈ രണ്ട് വരികൾ Pyrogram import ചെയ്യുന്നതിന് മുൻപ് തന്നെ വരണം
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
import re
import math
from pyrogram import Client, filters
from aiohttp import web

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://trenda-movie-bot.onrender.com")

# നിന്റെ ചാനലിന്റെ ഐഡി
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "-1004402285436")

bot = Client("trenda_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ടെലിഗ്രാമിന്റെ ഡാറ്റാ ചങ്ക് സൈസ് (1 MB)
CHUNK_SIZE = 1024 * 1024 

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! Trenda Bot is ready. Send me an MP4 movie! 🍿")

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    try:
        m = await message.reply_text("⏳ Processing your video securely... Please wait.")
        
        if str(CHANNEL_USERNAME).lstrip('-').isdigit():
            target_chat = int(CHANNEL_USERNAME)
        else:
            target_chat = CHANNEL_USERNAME
            
        copied_msg = await message.copy(chat_id=target_chat)
        link = f"{URL}/stream/{target_chat}/{copied_msg.id}"
        
        await m.edit_text(f"✅ **Your Permanent Direct Stream Link:**\n\n`{link}`\n\nPaste this in your admin panel!")
    except Exception as e:
        await message.reply_text(f"❌ Error saving to channel: {e}\n\n⚠️ Make sure the bot is an **ADMIN** in your channel!")

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Trenda Streaming Server is Live!")

@routes.get("/api/shorts")
async def get_shorts(request):
    try:
        links = []
        target_chat = int(CHANNEL_USERNAME) if str(CHANNEL_USERNAME).lstrip('-').isdigit() else CHANNEL_USERNAME
        async for msg in bot.get_chat_history(target_chat, limit=20):
            if msg.video or msg.document:
                link = f"{URL}/stream/{target_chat}/{msg.id}"
                links.append(link)
                
        headers = {"Access-Control-Allow-Origin": "*"}
        return web.json_response(links, headers=headers)
    except Exception:
        return web.json_response({"error": "Failed"}, status=500, headers={"Access-Control-Allow-Origin": "*"})

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
        
        if file_size > 2000 * 1024 * 1024:
            return web.Response(status=403, text="Error: File size exceeds 2GB limit.")
        
        range_header = request.headers.get('Range', '')
        forced_filename = "trenda_movie.mp4"
        
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
                'Content-Disposition': f'inline; filename="{forced_filename}"',
                'Access-Control-Allow-Origin': '*'
            }
            response = web.StreamResponse(status=206, headers=headers)
            await response.prepare(request)
            
            # --- SUPER FIX FOR LARGE MOVIES ---
            # ബൈറ്റ് നമ്പറുകളെ കൃത്യമായ ചങ്ക് നമ്പറുകളാക്കി മാറ്റുന്നു!
            chunk_offset = start // CHUNK_SIZE
            skip_bytes = start % CHUNK_SIZE
            bytes_to_send = length
            
            try:
                async for chunk in bot.stream_media(file.file_id, offset=chunk_offset):
                    if not chunk:
                        break
                    
                    if skip_bytes > 0:
                        chunk = chunk[skip_bytes:]
                        skip_bytes = 0
                        
                    if len(chunk) > bytes_to_send:
                        chunk = chunk[:bytes_to_send]
                        
                    await response.write(chunk)
                    bytes_to_send -= len(chunk)
                    
                    if bytes_to_send <= 0:
                        break
            except Exception:
                pass 
            return response
        else:
            headers = {
                'Accept-Ranges': 'bytes',
                'Content-Length': str(file_size),
                'Content-Type': 'video/mp4',
                'Content-Disposition': f'inline; filename="{forced_filename}"',
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
