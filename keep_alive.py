"""
🌐 Advanced Keep Alive Server - For Render
With System Stats (CPU, RAM, Storage), Auto-Ping, and Auto-Restart Protection
"""

import os
import sys
import time
import psutil
import logging
import requests
from threading import Thread
from flask import Flask

# Flask logging ko disable karna taaki console clean rahe
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Config
MAX_MEMORY_MB = 480.0  # 512MB Render limit hai, 480MB par auto-restart hoga

@app.route('/')
def home():
    """Webpage par System Stats dikhata hai"""
    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Memory (Total System Virtual Memory)
    mem = psutil.virtual_memory()
    mem_used_mb = mem.used / (1024 * 1024)
    mem_total_mb = mem.total / (1024 * 1024)
    
    # Current Bot Process Memory (Jo exact memory bot use kar raha hai)
    process = psutil.Process(os.getpid())
    bot_mem_mb = process.memory_info().rss / (1024 * 1024)
    
    # Storage
    disk = psutil.disk_usage('/')
    disk_used_gb = disk.used / (1024**3)
    disk_total_gb = disk.total / (1024**3)

    # Simple HTML UI
    html = f"""
    <html>
        <head>
            <title>Bot Status Dashboard</title>
            <meta http-equiv="refresh" content="30"> </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #121212; color: #ffffff;">
            <h2 style="color: #4CAF50;">🚀 Advanced PDF Bot is Alive!</h2>
            <div style="background: #1e1e1e; padding: 20px; border-radius: 10px; max-width: 500px; border: 1px solid #333;">
                <h3 style="border-bottom: 1px solid #444; padding-bottom: 10px;">📊 System Live Stats</h3>
                <p><b>🧠 CPU Usage:</b> {cpu_usage}%</p>
                <p><b>🤖 Bot RAM Usage:</b> <span style="color: {'#ff4444' if bot_mem_mb > 400 else '#4CAF50'}">{bot_mem_mb:.2f} MB</span> / {MAX_MEMORY_MB} MB Limit</p>
                <p><b>💾 System RAM:</b> {mem_used_mb:.2f} MB / {mem_total_mb:.2f} MB</p>
                <p><b>💽 Storage Usage:</b> {disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB ({disk.percent}%)</p>
                <br>
                <p style="font-size: 12px; color: #888;"><i>Page auto-refreshes every 30 seconds.</i></p>
            </div>
        </body>
    </html>
    """
    return html

def run():
    # Render dynamic PORT assign karta hai, default 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def auto_ping():
    """Har 10 minute me bot ko ping karta hai"""
    # Render apna URL RENDER_EXTERNAL_URL variable me deta hai
    url = os.environ.get("RENDER_EXTERNAL_URL", "http://127.0.0.1:8080")
    while True:
        time.sleep(600)  # 600 seconds = 10 minutes
        try:
            requests.get(url, timeout=10)
            print(f"🔄 Auto-Ping Success: {url}")
        except Exception as e:
            print(f"⚠️ Auto-Ping Failed: {e}")

def memory_monitor():
    """Bot ki memory check karta hai, limit cross hone par Auto-Restart karta hai"""
    while True:
        time.sleep(30) # Har 30 second me check karo
        try:
            process = psutil.Process(os.getpid())
            bot_mem_mb = process.memory_info().rss / (1024 * 1024)
            
            if bot_mem_mb >= MAX_MEMORY_MB:
                print(f"🚨 CRITICAL WARNING: Memory reached {bot_mem_mb:.2f}MB!")
                print("🔄 AUTO-RESTARTING BOT TO PREVENT RENDER CRASH...")
                
                # Yeh Python script ko forcefully nayi shuruaat se start kar dega
                os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f"⚠️ Memory Monitor Error: {e}")

def keep_alive():
    """Sab kuch ek sath background threads me start karne ka function"""
    # 1. Start Web Server
    t_web = Thread(target=run)
    t_web.daemon = True 
    t_web.start()
    
    # 2. Start Auto Pinger
    t_ping = Thread(target=auto_ping)
    t_ping.daemon = True
    t_ping.start()
    
    # 3. Start Memory Monitor (Auto-Restart Guard)
    t_monitor = Thread(target=memory_monitor)
    t_monitor.daemon = True
    t_monitor.start()
    
    print("🌐 Keep-Alive Server Started! Web UI, Auto-Ping & RAM Monitor Active.")