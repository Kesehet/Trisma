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

# Flask Setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Debug Mode
DEBUG = True

# Shared Variables (Thread-Safe)
image_data = None  # Stores received image
display_lock = asyncio.Lock()  # Prevents race conditions
mouse_event = None  # Stores mouse event

# Network Configuration
HOST = "0.0.0.0"
min_port, max_port = 1000, 65530
IMAGE_RECEIVER_PORT = 1111
IMAGE_SENDER_PORT = 2222
CONTROL_PORT = 3333
CONTROL_SENDER_PORT = 4444

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
    "server_uri": get_ip_address()
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
    last_event = None
    try:
        while True:
            if mouse_event and mouse_event != last_event:
                await websocket.send(json.dumps(mouse_event))
                last_event = mouse_event
            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosed:
        print("❌ Mouse control sender disconnected.")

async def handle_mouse_control(websocket):
    global mouse_event
    global image_data
    print("🖱️ Connected for receiving mouse control")
    try:
        async for message in websocket:
            messageNow = json.loads(message)
            try:
                mouse_event = messageNow
                image_data = None
            except json.JSONDecodeError:
                print("❌ Invalid mouse event received.")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Mouse control receiver disconnected.")

async def send_image(websocket):
    print("🌆 Image WebSocket connected for Browser")
    try:
        while True:
            async with display_lock:
                if image_data:
                    await websocket.send(image_data)
            await asyncio.sleep(1 / config["refresh_rate"])
    except websockets.exceptions.ConnectionClosed:
        print("❌ Image WebSocket disconnected.")

async def start_websockets():
    print("🚀 Starting WebSocket servers...")
    try:
        await asyncio.gather(
            websockets.serve(receive_and_store_image, HOST, IMAGE_RECEIVER_PORT),
            websockets.serve(handle_mouse_control, HOST, CONTROL_PORT),
            websockets.serve(send_mouse_control, HOST, CONTROL_SENDER_PORT),
            websockets.serve(send_image, HOST, IMAGE_SENDER_PORT)
        )
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
    print(f"🚀 Flask running at http://{HOST}:{config.get("web_interface_port")}")
    socketio.run(app, host='0.0.0.0', port=8080, debug=DEBUG, use_reloader=False)



# Main Execution
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_websockets())
    threading.Thread(target=run_flask, daemon=True).start()
    loop.run_forever()
