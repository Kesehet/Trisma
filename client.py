import asyncio
import requests
import websockets
import mss
import time
import json
import io
from PIL import Image
import pyautogui
import zlib

# Configuration
BASE_URI = "localhost"
WEB_INTERFACE_PORT = 8080
WEB_URI = f"http://{BASE_URI}:{WEB_INTERFACE_PORT}"
CONTROL_SENDER_PORT = 4444
IMAGE_RECEIVER_PORT = 1111

LAST_CONTROL_SENDER_PORT = CONTROL_SENDER_PORT
LAST_IMAGE_RECEIVER_PORT = IMAGE_RECEIVER_PORT


pyautogui.FAILSAFE = False


SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
SCREEN_RESOLUTION_MULTIPLIER = 1
REFRESH_RATE = 15

async def safe_websocket_connect(uri, retries=5, delay=3):
    """Attempts to connect to a WebSocket with retries."""
    for attempt in range(retries):
        try:
            websocket = await websockets.connect(uri, ping_interval=10, ping_timeout=20)
            print(f"✅ Connected to {uri} safely.")
            return websocket
        except Exception as e:
            print(f"❌ Failed to connect to {uri} (Attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(delay)
    print("❌ Maximum retries reached. Exiting.")
    return None

async def capture_and_send():
    """Captures the screen and sends images over WebSocket with reconnect logic."""
    global SCREEN_RESOLUTION_MULTIPLIER
    URI = f"ws://{BASE_URI}:{IMAGE_RECEIVER_PORT}"
    print(f"⚙ Connecting to {URI} for Image Streaming")

    websocket = await safe_websocket_connect(URI)
    if not websocket:
        return

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                start_time = time.time()
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                img = img.resize((
                    int(SCREEN_WIDTH * SCREEN_RESOLUTION_MULTIPLIER),
                    int(SCREEN_HEIGHT * SCREEN_RESOLUTION_MULTIPLIER)
                ))

                img_buffer = io.BytesIO()
                img.save(img_buffer, format="JPEG", quality=50)
                # print(f"🌆 Sending image of size: {len(img_buffer.getvalue())} bytes")
                compressed_data = zlib.compress(img_buffer.getvalue(), level=9)
                await websocket.send(compressed_data)

                elapsed_time = time.time() - start_time
                await asyncio.sleep(max(0, 1 / REFRESH_RATE - elapsed_time))
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                await asyncio.sleep(5)

async def receive_mouse_control():
    """Receives mouse movements and moves the client mouse."""
    URI = f"ws://{BASE_URI}:{CONTROL_SENDER_PORT}"
    websocket = await safe_websocket_connect(URI)
    if not websocket:
        return
    
    held_keys = set()
    modifier_keys = {"ctrl", "shift", "alt", "meta"}

    print("🖱️ Connected to mouse control WebSocket")
    async for message in websocket:
        try:
            data = json.loads(message)
            action = data.get("action", "")
            x = float(data.get("x", 0)) * SCREEN_WIDTH
            y = float(data.get("y", 0)) * SCREEN_HEIGHT
            button = data.get("button", "left")
            key = data.get("key", "").lower()
            data = json.loads(message)
            action = data.get("action", "")
            
            

            # Convert button codes to names
            button_map = {0: "left", 1: "middle", 2: "right"}
            button = button_map.get(button, "left")

            if action == "move":
                pyautogui.moveTo(x, y)  # Smooth movement
                

            elif action == "click":
                pyautogui.click(x, y, button=button)
                print(f"🖱️ Clicked at: ({x}, {y}) with {button} button")

            elif action == "mousedown":
                pyautogui.mouseDown(x, y, button=button)
                print(f"🖱️ Mouse down at: ({x}, {y}) with {button} button")
                

            elif action == "mouseup":
                pyautogui.mouseUp(x, y, button=button, duration=0)
                print(f"🖱️ Mouse up at: ({x}, {y}) with {button} button")

            elif action == "dblclick":
                pyautogui.doubleClick(x, y)
                # print(f"🖱️ Double clicked at: ({x}, {y})")

            elif action == "rightclick":
                pyautogui.rightClick(x, y)
                # print(f"🖱️ Right clicked at: ({x}, {y})")

            elif action == "click":
                x = float(data.get("x", 0)) * SCREEN_WIDTH
                y = float(data.get("y", 0)) * SCREEN_HEIGHT
                button = data.get("button", "left")
                pyautogui.click(x, y, button=button)

            

            if action == "keydown":
                if key in modifier_keys:
                    pyautogui.keyDown(key)  # Hold modifier key
                    held_keys.add(key)
                else:
                    pyautogui.keyDown(key)

            if action == "keyup":
                if key in held_keys:
                    pyautogui.keyUp(key)  # Release modifier key
                    held_keys.remove(key)
                else:
                    pyautogui.keyUp(key)
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️ Invalid mouse message format: {message} - Error: {e}")

def load_config():
    try:
        print(f"Fetching config from {WEB_URI}/config")
        resp = requests.get(f"{WEB_URI}/config").json()
        print(f"Received config: {resp}")
        return resp
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching config: {e}")
        return {}

async def restart_websockets():
    """Cancels existing WebSocket tasks and restarts them with new ports."""
    global websocket_tasks

    # Cancel existing tasks
    for task in websocket_tasks:
        task.cancel()
    await asyncio.sleep(1)  # Allow cancellation to process

    # Restart WebSocket connections
    websocket_tasks = [
        asyncio.create_task(capture_and_send()),
        asyncio.create_task(receive_mouse_control())
    ]
    print("🔄 WebSocket connections restarted.")


async def set_config():
    """Fetches and updates configuration from the server, restarting WebSockets if necessary."""
    global SCREEN_RESOLUTION_MULTIPLIER, REFRESH_RATE, CONTROL_SENDER_PORT, IMAGE_RECEIVER_PORT
    global BASE_URI, LAST_CONTROL_SENDER_PORT, LAST_IMAGE_RECEIVER_PORT
    while True:
        try:
            resp = load_config()
            SCREEN_RESOLUTION_MULTIPLIER = float(resp.get("resolution_multiplier", SCREEN_RESOLUTION_MULTIPLIER))
            REFRESH_RATE = float(resp.get("refresh_rate", REFRESH_RATE))
            new_control_sender_port = resp.get("control_sender_port", CONTROL_SENDER_PORT)
            new_image_receiver_port = resp.get("image_receiver_port", IMAGE_RECEIVER_PORT)
            BASE_URI = resp.get("server_uri", BASE_URI)

            # Detect if ports have changed
            if new_control_sender_port != CONTROL_SENDER_PORT or new_image_receiver_port != IMAGE_RECEIVER_PORT:
                print("⚠️ Detected port change. Restarting WebSocket connections...")
                
                # Update ports
                CONTROL_SENDER_PORT = new_control_sender_port
                IMAGE_RECEIVER_PORT = new_image_receiver_port
                
                # Restart tasks safely
                await restart_websockets()

        except Exception as e:
            print(f"❌ Error loading config: {e}")

        await asyncio.sleep(3)  # Refresh config every 3 seconds


websocket_tasks = []
  

async def main():
    """Runs both screen streaming and mouse control tasks with dynamic reconnections."""
    global WEB_URI, BASE_URI, WEB_INTERFACE_PORT
    base_ip = input("Enter the server IP: ")
    base_port = input("Enter the server port: ")
    WEB_INTERFACE_PORT = base_port
    BASE_URI = base_ip
    WEB_URI = f"http://{base_ip}:{base_port}"

    global websocket_tasks
    websocket_tasks = [
        asyncio.create_task(capture_and_send()),
        asyncio.create_task(receive_mouse_control()),
        asyncio.create_task(set_config())  # Monitors config changes
    ]

    await asyncio.gather(*websocket_tasks)


if __name__ == "__main__":
    asyncio.run(main())