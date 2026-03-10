"""
🤖 Advanced Bulk PDF Merger Bot
A smart bot that merges a base PDF with bulk target PDFs efficiently.
Supports Custom Output File Naming, Anti-Spam Logic & Dynamic Aesthetic Metadata.
"""

import os
import sys
import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
    
import time
from typing import Optional, Dict

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message,
    CallbackQuery
)
from pyrogram.errors import MessageNotModified, FloodWait

# pypdf import kiya hai taaki output PDF ka metadata read kar sakein
from pypdf import PdfReader 

# Import local modules
from keep_alive import keep_alive
from config import config
from database import db
from pdf_processor import pdf_processor

# ============== GLOBAL STATE & LOCKS ==============
class UserState:
    def __init__(self):
        self.states = {}
    def set(self, user_id, state):
        self.states[user_id] = state
    def get(self, user_id):
        return self.states.get(user_id)
    def clear(self, user_id):
        self.states.pop(user_id, None)

state_manager = UserState()

# Anti-Spam Queue Message Tracker & Locks
user_queue_msgs = {} # {user_id: Message object}
user_locks = {}      # {user_id: asyncio.Lock}

def get_user_lock(user_id):
    """User ke liye ek unique lock banata hai taaki bulk forward me crash na ho"""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

# ============== UTILS ==============
def clean_file(path: str):
    """File delete karne ka simple function taaki server clean rahe"""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except: pass

async def progress_tracker(current, total, msg_obj, action_text):
    """Real-time Progress dikhane ke liye"""
    try:
        percent = round((current / total) * 100, 1)
        # Har 20% par update karega taaki Telegram FloodWait na de
        if percent % 20 == 0 or percent == 100:  
            text = f"⏳ **{action_text}**\n\nProgress: `{percent}%`"
            await msg_obj.edit(text)
    except MessageNotModified:
        pass
    except FloodWait:
        pass # Progress update skip kar do agar rate limit hit ho

# ============== KEYBOARDS ==============

def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    settings = db.get_user_settings(user_id)
    pos_str = "Start (Pehle)" if settings["position"] == "start" else "End (Aakhir me)"
    prefix = settings["custom_prefix"]
    queue_len = len(db.get_queue(user_id))
    
    buttons = [
        [InlineKeyboardButton("📁 Set Base PDF", callback_data="set_base")],
        [InlineKeyboardButton(f"⚙️ Merge Position: {pos_str}", callback_data="toggle_pos")],
        [InlineKeyboardButton("📝 Set Custom File Name Prefix", callback_data="set_prefix")]
    ]
    
    if prefix:
        buttons.append([InlineKeyboardButton(f"🗑️ Remove Prefix ({prefix})", callback_data="remove_prefix")])
    
    if queue_len > 0:
        buttons.append([InlineKeyboardButton(f"▶️ Merge All Pending ({queue_len} PDFs)", callback_data="process_queue")])
        buttons.append([InlineKeyboardButton("❌ Clear List", callback_data="clear_queue")])
        
    return InlineKeyboardMarkup(buttons)

# ============== BOT CLIENT ==============
app = Client(
    "pdf_merger_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# ============== COMMANDS ==============

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    db.register_user(user.id, user.username)
    state_manager.clear(user.id)
    
    settings = db.get_user_settings(user.id)
    base_name = settings['base_pdf_name'] if settings['base_pdf_path'] else "Abhi set nahi hai ❌"
    custom_prefix = settings['custom_prefix'] or "Exact Original Name (Kuch add nahi hoga)"

    text = f"""
👋 **Namaste {user.first_name}!**

Main ek **Advanced Bulk PDF Merger Bot** hu. 🚀

**Apni Settings Dekhein:**
📁 Base PDF: `{base_name}`
📝 Output Name: `{custom_prefix}`

**Kaise Use Karein?**
1️⃣ `Set Base PDF` pe click karein aur apna Base PDF bhejein.
2️⃣ File Name me kuch jodna ho toh `Set Custom File Name Prefix` dabayein.
3️⃣ `Merge Position` set karein (Pehle ya Aakhir me).
4️⃣ Ek sath bulk me apni PDFs bhejein.
5️⃣ Phir `Merge All Pending` dabayein!
"""
    await message.reply(text, reply_markup=main_menu_keyboard(user.id))

# ============== MESSAGE HANDLERS ==============

@app.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    state = state_manager.get(user_id)
    
    if state == "waiting_prefix":
        prefix = message.text.strip()
        db.update_prefix(user_id, prefix)
        state_manager.clear(user_id)
        
        await message.reply(
            f"✅ **Prefix Set Ho Gaya!**\n\nAb aapki nayi files ka naam hoga: `{prefix}_original_filename.pdf`",
            reply_markup=main_menu_keyboard(user_id)
        )

@app.on_message(filters.document & filters.private)
async def handle_docs(client: Client, message: Message):
    user_id = message.from_user.id
    doc = message.document
    
    if not doc.file_name.lower().endswith('.pdf'):
        await message.reply("⚠️ **Kripya sirf PDF file bhejein!**")
        return
        
    state = state_manager.get(user_id)
    
    # 1. Agar Base PDF set kar raha hai
    if state == "waiting_base_pdf":
        state_manager.clear(user_id)
        msg = await message.reply("📥 **Base PDF Download ho raha hai...**")
        try:
            os.makedirs(config.USER_BASE_DIR, exist_ok=True)
            file_name = f"base_{user_id}_{int(time.time() * 1000)}.pdf"
            path = os.path.join(config.USER_BASE_DIR, file_name)
            
            await client.download_media(message, file_name=path, progress=progress_tracker, progress_args=(msg, "Downloading Base PDF..."))
            
            if not pdf_processor.is_valid_pdf(path):
                clean_file(path)
                await msg.edit("❌ **Ye PDF file corrupt hai ya password protected hai. Kripya dusri file bhejein.**")
                return

            db.set_base_pdf(user_id, path, doc.file_name)
            
            await msg.edit(
                f"✅ **Base PDF Successfully Set Ho Gaya!**\n\n📄 File: `{doc.file_name}`\n\nAb aap jitni chahe Target PDFs bhej sakte hain (Bulk me).",
                reply_markup=main_menu_keyboard(user_id)
            )
        except Exception as e:
            await msg.edit(f"❌ **Error:** {str(e)}")
        return

    # 2. Agar bulk target PDFs bhej raha hai
    settings = db.get_user_settings(user_id)
    if not settings["base_pdf_path"] or not os.path.exists(settings["base_pdf_path"]):
        await message.reply("⚠️ **Aapne Base PDF set nahi kiya hai!**\n\nPehle menu se `Set Base PDF` par click karein.")
        return
        
    # LOCK SYSTEM: Taki ek sath 20 file aane par crash na ho
    lock = get_user_lock(user_id)
    async with lock:
        db.add_to_queue(user_id, doc.file_id, doc.file_name, doc.file_size)
        queue_len = len(db.get_queue(user_id))
        
        display_name = doc.file_name[:30] + "..." if len(doc.file_name) > 30 else doc.file_name
        text = f"✅ **PDF List me add ho gayi!**\n📄 Last added: `{display_name}`\n📦 Total Pending Files: **{queue_len}**\n\nAur bhejein, ya 'Merge All Pending' dabayein."
        markup = main_menu_keyboard(user_id)
        
        try:
            if user_id in user_queue_msgs:
                last_msg = user_queue_msgs[user_id]
                await last_msg.edit_text(text, reply_markup=markup)
            else:
                msg = await message.reply(text, reply_markup=markup)
                user_queue_msgs[user_id] = msg
        except FloodWait:
            pass
        except MessageNotModified:
            pass
        except Exception:
            msg = await message.reply(text, reply_markup=markup)
            user_queue_msgs[user_id] = msg

# ============== CALLBACK HANDLERS ==============

@app.on_callback_query()
async def callbacks(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        if data == "set_base":
            state_manager.set(user_id, "waiting_base_pdf")
            await callback.message.edit(
                "📁 **Kripya apni Base PDF yaha bhejein...**\n\n(Nayi file bhejte hi purani wali automatically delete ho jayegi)"
            )
            
        elif data == "toggle_pos":
            settings = db.get_user_settings(user_id)
            new_pos = "end" if settings["position"] == "start" else "start"
            db.update_position(user_id, new_pos)
            await callback.answer(f"Position update ho gayi: {new_pos.title()}")
            await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard(user_id))
            
        elif data == "set_prefix":
            state_manager.set(user_id, "waiting_prefix")
            await callback.message.edit(
                "📝 **Apna Custom Prefix type karke bhejein:**\n\nJaise ki aapka brand name ya apna naam. Wo har file ke shuru me lag jayega."
            )
            
        elif data == "remove_prefix":
            db.update_prefix(user_id, None)
            await callback.answer("Prefix hata diya gaya hai!")
            await callback.message.edit(
                "✅ **Prefix Remove ho gaya!**\nAb aapki files usi naam se aayengi jis naam se aapne bheji thi (Exact original name).",
                reply_markup=main_menu_keyboard(user_id)
            )
            
        elif data == "clear_queue":
            db.clear_queue(user_id)
            user_queue_msgs.pop(user_id, None)
            await callback.answer("Saari pending list delete kar di gayi!")
            await callback.message.edit("🗑️ **Queue clear ho gayi hai.**\nAap fir se nayi files bhej sakte hain.", reply_markup=main_menu_keyboard(user_id))
            
        elif data == "process_queue":
            user_queue_msgs.pop(user_id, None)
            await process_bulk_queue(client, callback.message, user_id)
            
    except MessageNotModified: pass
    except Exception as e:
        print(f"Callback Error: {e}")

# ============== BULK PROCESSING ENGINE ==============

def clean_pdf_date(d_str):
    """PDF ke ajeeb dates (e.g. D:20260310230706) ko thoda saaf karta hai"""
    if not d_str: return ""
    return str(d_str).replace("D:", "").replace("'", ":").split("+")[0].split("-")[0]

async def process_bulk_queue(client: Client, message: Message, user_id: int):
    settings = db.get_user_settings(user_id)
    base_pdf = settings["base_pdf_path"]
    position = settings["position"]
    custom_prefix = settings["custom_prefix"]
    
    if not base_pdf or not os.path.exists(base_pdf):
        await message.edit("⚠️ **Base PDF delete ho gaya ya mil nahi raha.** Kripya wapas `Set Base PDF` karein.")
        return
        
    queue = db.get_queue(user_id)
    total = len(queue)
    if total == 0:
        await message.edit("⚠️ **Queue bilkul khali hai!**", reply_markup=main_menu_keyboard(user_id))
        return
        
    status_msg = await message.edit(f"🚀 **PDF Processing Shuru Ho Gaya...**\n\nTotal Files: {total}")
    success_count = 0
    
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    for i, item in enumerate(queue):
        item_id = item["id"]
        file_id = item["file_id"]
        orig_name = item["file_name"]
        
        try:
            await status_msg.edit(f"⚙️ **Processing {i+1} of {total}**\n\n📄 File: `{orig_name}`\n⬇️ Downloading...")
            await asyncio.sleep(1) 
        except FloodWait as e:
            await asyncio.sleep(e.value)
            
        if custom_prefix:
            display_out_name = f"{custom_prefix}_{orig_name}"
        else:
            display_out_name = orig_name
            
        local_target_path = os.path.join(config.TEMP_DIR, f"target_{user_id}_{int(time.time() * 1000)}_{i}.pdf")
        local_output_path = os.path.join(config.OUTPUT_DIR, f"merged_{user_id}_{int(time.time() * 1000)}_{i}.pdf")
        
        try:
            # 1. Download target PDF
            await client.download_media(file_id, file_name=local_target_path)
            
            # 2. Merge Pages
            try:
                await status_msg.edit(f"⚙️ **Processing {i+1} of {total}**\n\n📄 File: `{orig_name}`\n🔗 Processing PDF...")
            except: pass 
            
            result = pdf_processor.merge_pdfs(local_target_path, base_pdf, position, local_output_path)
            
            # 3. Upload File to User with DYNAMIC Aesthetic Metadata
            if result["success"]:
                
                # --- AESTHETIC DYNAMIC METADATA EXTRACTION LOGIC ---
                meta_text = f"╭━━━ [ 📄 **File Details** ] ━━━\n"
                meta_text += f"┣ 🏷️ **Name:** `{display_out_name}`\n"
                
                try:
                    # File Size Extraction
                    file_size_kb = os.path.getsize(local_output_path) / 1024
                    size_str = f"{file_size_kb:.2f} KB" if file_size_kb < 1024 else f"{(file_size_kb/1024):.2f} MB"
                    meta_text += f"┣ 💾 **Size:** `{size_str}`\n"
                    
                    reader = PdfReader(local_output_path)
                    pages = len(reader.pages)
                    meta_text += f"┣ 📑 **Pages:** `{pages}`\n"
                    
                    # 🚀 FULL DYNAMIC LIVE METADATA SCANNER
                    meta = reader.metadata
                    if meta:
                        # Aesthetic Emojis for known keys, default for unknown
                        emoji_map = {
                            "Title": "📌", "Author": "👤", "Subject": "📝",
                            "Keywords": "🔑", "Creator": "🛠️", "Producer": "⚙️",
                            "CreationDate": "📅", "ModDate": "🕒", "Company": "🏢",
                            "Source": "🌐"
                        }
                        
                        for raw_key, value in meta.items():
                            if not value: # Agar value khali hai toh skip karo
                                continue
                                
                            # Key ko clean karna (e.g. "/CreationDate" -> "CreationDate")
                            clean_key = str(raw_key).replace("/", "").strip()
                            
                            # Value ko clean karna aur dates ko fix karna
                            clean_val = str(value).strip()
                            if "Date" in clean_key:
                                clean_val = clean_pdf_date(clean_val)
                                
                            # Agar metadata bohot bada ho (jaise 100 words ke keywords) toh design kharab na ho
                            if len(clean_val) > 50:
                                clean_val = clean_val[:47] + "..."
                                
                            # Dynamic Emoji Matcher
                            emoji = emoji_map.get(clean_key, "🔸")
                            
                            # Final aesthetic line
                            meta_text += f"┣ {emoji} **{clean_key}:** `{clean_val}`\n"
                            
                except Exception as e:
                    print(f"Metadata fetch error: {e}")
                
                # Channel Branding at the bottom
                channel_username = os.getenv("CHANNEL_USERNAME", "YourChannelName")
                meta_text += f"╰━━━━━━━━━━━━━━━━━━━━━━\n"
                meta_text += f"📢 **Channel:** {channel_username}"
                
                try:
                    await status_msg.edit(f"⚙️ **Processing {i+1} of {total}**\n\n📄 File: `{orig_name}`\n⬆️ Uploading to Telegram...")
                except: pass
                
                await client.send_document(
                    chat_id=user_id,
                    document=local_output_path,
                    file_name=display_out_name,
                    caption=meta_text # Naya 100% Dynamic Caption
                )
                success_count += 1
                db.remove_from_queue(item_id)
            else:
                await client.send_message(user_id, f"❌ **Fail ho gaya:** `{orig_name}`\nReason: PDF corrupt ho sakti hai.")
                db.remove_from_queue(item_id)
                
        except FloodWait as e:
            await asyncio.sleep(e.value + 2) 
        except Exception as e:
            print(f"Error processing file {orig_name}: {e}")
            await client.send_message(user_id, f"❌ **Error aa gaya:** `{orig_name}` me.")
            db.remove_from_queue(item_id)
            
        finally:
            clean_file(local_target_path)
            clean_file(local_output_path)


    # ==========================================
    # 🎯 UX FIX: MESSAGE AT THE BOTTOM
    # ==========================================
    
    try:
        await status_msg.delete()
    except:
        pass
        
    final_text = (
        f"🎉 **Batch Complete!**\n\n"
        f"✅ Successfully Processed: **{success_count}/{total}** PDFs.\n\n"
        f"👇 **Aap aur files upload kar sakte hain ya niche se options select karein:**"
    )
    
    try:
        await client.send_message(
            chat_id=user_id,
            text=final_text,
            reply_markup=main_menu_keyboard(user_id)
        )
    except Exception as e:
        print(f"Final message sending error: {e}")
    
    # Auto-Cleanup to save storage
    try:
        config.run_auto_cleanup()
    except Exception as e:
        print(f"Cleanup trigger error: {e}")

# ============== MAIN ENTRY ==============

def main():
    print("\n🚀 Starting Fast Bulk PDF Merger Bot...")
    if not config.validate(): sys.exit(1)
    config.create_directories()
    
    # 🌐 START KEEP-ALIVE SERVER (For Render)
    keep_alive()
    
    app.run()

if __name__ == "__main__":
    main()