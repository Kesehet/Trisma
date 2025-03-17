import asyncio
import random
import websockets
import io
import json
import threading
from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO
from PIL import Image
import requests
import zlib
import socket

# Flask Setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Debug Mode
DEBUG = False

# Shared Variables (Thread-Safe)
image_data = None  # Stores received image
display_lock = asyncio.Lock()  # Prevents race conditions
mouse_event = None  # Stores mouse event
image_updated = asyncio.Event()  # Global Event for image update
mouse_event_updated = asyncio.Event()

# Network Configuration
HOST = "0.0.0.0"
min_port, max_port = 1000, 65530
IMAGE_RECEIVER_PORT = 1111
IMAGE_SENDER_PORT = 2222
CONTROL_PORT = 3333
CONTROL_SENDER_PORT = 4444
VOICE_SENDER_PORT = 5555

def get_ip_address():
    '''Get public IP address'''
    if DEBUG:
        return '127.0.0.1'
    return requests.get('https://api64.ipify.org').text

config = {
    "host": HOST,
    "image_receiver_port": IMAGE_RECEIVER_PORT,
    "image_sender_port": IMAGE_SENDER_PORT,
    "control_port": CONTROL_PORT,
    "control_sender_port": CONTROL_SENDER_PORT,
    "resolution_multiplier": 1,
    "refresh_rate": 10,
    "server_uri": get_ip_address(),
    "voice_sender_port" : VOICE_SENDER_PORT,
}

# WebSocket Handlers
async def receive_and_store_image(websocket):
    global image_data
    print("📡 Connected for screen streaming")
    last_image_data = None
    try:
        async for message in websocket:
            # if len(message) > 5 * 1024 * 1024:
            #     print("⚠ Warning: Large image, dropping frame.")
            #     continue
            if message != last_image_data:
                async with display_lock:
                    image_data = message
                last_image_data = message
                image_updated.set()  # Notify image sender
                await websocket.pong()
    except websockets.exceptions.ConnectionClosedError:
        print("❌ Client disconnected unexpectedly!")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("🔌 Connection closed.")

async def send_mouse_control(websocket):
    global mouse_event
    print("🖱️ Connected for mouse control sending")
    try:
        while True:
            await mouse_event_updated.wait()
            await websocket.send(json.dumps(mouse_event))
            mouse_event_updated.clear()
    except websockets.exceptions.ConnectionClosed:
        print("❌ Mouse control sender disconnected.")

async def handle_mouse_control(websocket):
    global mouse_event
    print("🖱️ Connected for receiving mouse control")
    try:
        async for message in websocket:
            messageNow = json.loads(message)
            mouse_event = messageNow
            mouse_event_updated.set()  # Notify sender
    except websockets.exceptions.ConnectionClosed:
        print("❌ Mouse control receiver disconnected.")


async def send_image(websocket):
    print("🌆 Image WebSocket connected for Browser")
    try:
        while True:
            await image_updated.wait()  # Wait for an image update
            async with display_lock:
                if image_data:
                    await websocket.send(zlib.decompress(image_data))
            image_updated.clear()  # Reset the event after sending
    except websockets.exceptions.ConnectionClosed:
        print("❌ Image WebSocket disconnected.")

# Store connected clients
voice_clients = set()

async def audio_handler(websocket):
    global voice_clients
    print(f"🎤 Connected {len(voice_clients)} clients for voice chat")
    voice_clients.add(websocket)
    try:
        async for message in websocket:
            # Forward audio to all connected browser clients
            websockets.broadcast(voice_clients, message)
    except websockets.exceptions.ConnectionClosed:
        print("❌ Audio client disconnected.")
    finally:
        voice_clients.remove(websocket)
        print("🔌 Audio connection closed.")



async def start_websockets():
    print("🚀 Starting WebSocket servers...")
    try:
        servers = [
            websockets.serve(receive_and_store_image, HOST, IMAGE_RECEIVER_PORT),
            websockets.serve(handle_mouse_control, HOST, CONTROL_PORT),
            websockets.serve(send_mouse_control, HOST, CONTROL_SENDER_PORT),
            websockets.serve(send_image, HOST, IMAGE_SENDER_PORT),
            websockets.serve(audio_handler, HOST, VOICE_SENDER_PORT)
        ]
        await asyncio.gather(*servers)
        print("✅ WebSocket servers started successfully.")
    except Exception as e:
        print(f"❌ WebSocket startup failed: {e}")

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/config", methods=["GET", "POST"])
def get_config():
    global config
    if request.method == "POST":
        config.update(request.get_json())
    return json.dumps(config)

# Run Flask in a Separate Thread
def run_flask():
    print(f"🚀 Flask running at http://{HOST}:{config.get('web_interface_port')}")
    socketio.run(app, host='0.0.0.0', port=config.get('web_interface_port'), debug=DEBUG, use_reloader=False)



# Main Execution
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_websockets())
    threading.Thread(target=run_flask, daemon=True).start()
    loop.run_forever()
