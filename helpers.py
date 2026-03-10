"""
🛠️ Helper Utilities - Premium PDF Bot
Common utility functions and decorators
"""

import os
import time
import logging
import functools
from typing import Callable
from datetime import datetime
from pyrogram.types import Message

# Bot ke liye standard logging setup (Print se better aur safe hota hai)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def admin_only(func: Callable):
    """
    Decorator to restrict command to admin users only
    Usage: @admin_only
    """
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        try:
            from config import config
            
            # Check: Agar message channel ya anonymous admin se hai toh from_user 'None' ho sakta hai
            user_id = message.from_user.id if message.from_user else None
            
            if not user_id or user_id not in config.ADMIN_IDS:
                await message.reply(
                    "⛔ **Access Denied!**\n\n"
                    "This command is only for administrators.",
                    parse_mode="Markdown" # Default markdown use kiya hai
                )
                return
            
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in admin_only decorator: {e}")
            # Agar koi error aaye toh user ko alert kar do but crash na ho
            await message.reply("⚠️ An error occurred while verifying permissions.")
    
    return wrapper

def log_user_action(action: str):
    """
    Decorator to log user actions
    Usage: @log_user_action("command_name")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            try:
                # Safe fallback agar from_user None hai
                user_name = message.from_user.first_name if message.from_user else "Unknown/Channel"
                user_id = message.from_user.id if message.from_user else "Unknown"
                
                logger.info(f"User {user_id} ({user_name}) - {action}")
            except Exception as e:
                logger.error(f"Error logging action: {e}")
                
            # Logging fail bhi ho jaye, phir bhi command run honi chahiye
            return await func(client, message, *args, **kwargs)
        
        return wrapper
    return decorator

def format_bytes(size: int) -> str:
    """Format bytes to human readable string"""
    # Type safety check
    if not isinstance(size, (int, float)):
        return "0 B"
        
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    # Ensure input string hi hai
    if not isinstance(text, str):
        text = str(text)
        
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def clean_temp_files(directory: str, max_age_hours: int = 24):
    """Clean old temporary files"""
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    logger.info(f"🧹 Cleaned: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error cleaning {filename}: {e}")

# Premium status messages
STATUS_MESSAGES = {
    "downloading": "📥 **Downloading...**\n\n{progress} {percent}%",
    "uploading": "📤 **Uploading...**\n\n{progress} {percent}%",
    "processing": "⚙️ **Processing...**\n\n_Please wait..._",
    "success": "✅ **Complete!**\n\n{details}",
    "error": "❌ **Error!**\n\n`{error}`",
}