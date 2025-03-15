import os
import sys
import requests
import asyncio
import websockets
import tkinter as tk
from tkinter import messagebox
import pyautogui
import time
import mss
from PIL import Image, ImageTk
import json

# Default Configuration
BASE_URI = "localhost"
WEB_URI = f"http://{BASE_URI}:8080"
CONTROL_SENDER_PORT = 9999
IMAGE_RECEIVER_PORT = 9998
SCREEN_RESOLUTION_MULTIPLIER = 1
REFRESH_RATE = 15

def get_config():
    """Fetches the configuration from the server and updates global variables."""
    global CONTROL_SENDER_PORT, IMAGE_RECEIVER_PORT, SCREEN_RESOLUTION_MULTIPLIER, REFRESH_RATE
    try:
        response = requests.get(f"{WEB_URI}/config", timeout=5).json()
        CONTROL_SENDER_PORT = response.get("control_sender_port", CONTROL_SENDER_PORT)
        IMAGE_RECEIVER_PORT = response.get("image_receiver_port", IMAGE_RECEIVER_PORT)
        SCREEN_RESOLUTION_MULTIPLIER = response.get("resolution_multiplier", SCREEN_RESOLUTION_MULTIPLIER)
        REFRESH_RATE = response.get("refresh_rate", REFRESH_RATE)
        return True
    except requests.RequestException:
        return False

def check_ping():
    """Check if the BASE_URI is reachable."""
    try:
        response = requests.get(WEB_URI, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_libraries = ["asyncio", "requests", "websockets", "mss", "pyautogui", "PIL"]
    missing_libraries = []

    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            missing_libraries.append(lib)

    return missing_libraries

def test_pyautogui():
    """Move the mouse and take a screenshot to verify pyautogui functionality."""
    try:
        screen_width, screen_height = pyautogui.size()
        
        # Move the mouse in a small loop
        pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=1)
        pyautogui.moveTo(screen_width // 3, screen_height // 3, duration=1)

        # Take a screenshot
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            return img
    except Exception as e:
        return f"Pyautogui Error: {e}"

async def test_websocket(port):
    """Check if the WebSocket server is reachable and disconnect after 5 seconds."""
    URI = f"ws://{BASE_URI}:{port}"
    try:
        async with websockets.connect(URI) as websocket:
            print(f"Connected to WebSocket server at {URI}")
            await asyncio.sleep(5)  # Stay connected for 5 seconds
            await websocket.close()
            print(f"Disconnected from WebSocket server at {URI}")
            return True
    except Exception as e:
        print(f"Failed to connect to WebSocket server at {URI}: {e}")
        return False

def display_results(ping_status, config_status, missing_libs, pyautogui_result, ws_control_status, ws_image_status):
    """Display test results using Tkinter GUI."""
    root = tk.Tk()
    root.title("Client.py Test Results")
    root.geometry("500x450")

    tk.Label(root, text="Client.py Test Results", font=("Arial", 14, "bold")).pack(pady=10)

    # Network Test
    tk.Label(root, text=f"Ping to Server: {'✅ Connected' if ping_status else '❌ Failed'}",
             fg="green" if ping_status else "red").pack()

    # Config Fetch Test
    tk.Label(root, text=f"Fetched Configuration: {'✅ Success' if config_status else '❌ Failed'}",
             fg="green" if config_status else "red").pack()

    # Dependency Check
    if missing_libs:
        lib_text = f"Missing Libraries: {', '.join(missing_libs)}"
        lib_label = tk.Label(root, text=lib_text, fg="red")
    else:
        lib_label = tk.Label(root, text="All Dependencies Installed ✅", fg="green")
    lib_label.pack()

    # WebSocket Tests
    tk.Label(root, text=f"WebSocket (Control): {'✅ Connected' if ws_control_status else '❌ Failed'}",
             fg="green" if ws_control_status else "red").pack()

    tk.Label(root, text=f"WebSocket (Image Streaming): {'✅ Connected' if ws_image_status else '❌ Failed'}",
             fg="green" if ws_image_status else "red").pack()

    # Pyautogui Test
    if isinstance(pyautogui_result, str):
        screenshot_label = tk.Label(root, text=pyautogui_result, fg="red")
        screenshot_label.pack()
    else:
        tk.Label(root, text="Pyautogui Test Passed ✅", fg="green").pack()
        img = ImageTk.PhotoImage(pyautogui_result)
        panel = tk.Label(root, image=img)
        panel.image = img
        panel.pack()

    # Screen Resolution
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
    tk.Label(root, text="Screen Resolution:").pack()
    tk.Label(root, text=f"Screen Width: {SCREEN_WIDTH}, Height: {SCREEN_HEIGHT}", fg="green").pack()
    
    tk.Button(root, text="Close", command=root.quit).pack(pady=10)

    root.mainloop()

def main():
    print("Running client.py environment test...\n")

    # **Step 1: Check Network Connectivity**
    print("Checking connectivity to BASE_URI...")
    ping_status = check_ping()
    print("Ping successful!" if ping_status else "Ping failed!")

    # **Step 2: Get Configuration (Ports)**
    print("Fetching configuration from the server...")
    config_status = get_config()
    print(f"Configuration fetched: {config_status}")

    # **Step 3: Check Dependencies**
    print("Checking required dependencies...")
    missing_libs = check_dependencies()
    if missing_libs:
        print(f"Missing Libraries: {', '.join(missing_libs)}")
    else:
        print("All dependencies are installed.")

    # **Step 4: Test Pyautogui**
    print("Testing pyautogui functionality...")
    pyautogui_result = test_pyautogui()
    if isinstance(pyautogui_result, Image.Image):
        print("Pyautogui test passed!")
    else:
        print(pyautogui_result)

    # **Step 5: Test WebSockets (Control & Image Streaming)**
    print(f"Testing WebSocket connection to Control Server (Port {CONTROL_SENDER_PORT})...")
    ws_control_status = asyncio.run(test_websocket(CONTROL_SENDER_PORT))
    
    print(f"Testing WebSocket connection to Image Streaming Server (Port {IMAGE_RECEIVER_PORT})...")
    ws_image_status = asyncio.run(test_websocket(IMAGE_RECEIVER_PORT))

    # **Step 6: Display Results in GUI**
    display_results(ping_status, config_status, missing_libs, pyautogui_result, ws_control_status, ws_image_status)

main()