# 🤖 PDF Master Pro - Premium Telegram Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A Premium PDF Bot with Batch Processing & Auto Cleanup**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage)

</div>

---

## ✨ Features

### 🖼️ Default Image System
- **Set Once, Use Forever**: Save your cover image once
- **Auto Apply**: Image automatically applied to all PDFs
- **Easy Change**: Replace image anytime with one click
- **Smart Delete**: Old image auto-deleted when changing

### 📦 Batch Processing
- **Multiple PDFs**: Send multiple PDFs at once
- **Queue System**: PDFs processed one by one automatically
- **Progress Tracking**: See real-time progress updates
- **Auto Cleanup**: Files deleted after each processing

### ⚡ Fast & Efficient
- **Auto Server Cleanup**: Perfect for free tier servers
- **Memory Optimized**: Minimal storage usage
- **Quick Processing**: Fast PDF manipulation

### 🎨 Premium UI
- Beautiful button navigation
- Clean message formatting
- Real-time status updates

---

## 🚀 Installation

### Step 1: Get API Credentials

#### Get API_ID and API_HASH:
1. Go to https://my.telegram.org/apps
2. Login with your Telegram account
3. Create a new application
4. Copy `api_id` and `api_hash`

#### Get BOT_TOKEN:
1. Open @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions and copy token

### Step 2: Setup Bot

```bash
# Navigate to bot folder
cd telegram-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Edit .env file
nano .env
```

### Step 3: Configure .env

```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_telegram_user_id
```

### Step 4: Run Bot

```bash
python3 main.py
```

---

## 📱 How To Use

### First Time Setup
1. Start bot with `/start`
2. Click **"📸 Set Image"**
3. Send your cover image
4. Done! Image saved for all future PDFs

### Process PDFs
1. Send one or multiple PDF files
2. Click **"✅ Process Now"**
3. Receive processed PDFs one by one
4. Files auto-deleted after processing!

### Change Default Image
1. Click **"🔄 Change Image"**
2. Send new image
3. Old image deleted, new one saved!

### Remove Default Image
1. Click **"🗑️ Remove Image"**
2. Image deleted from server

---

## 🎛️ Settings

| Setting | Options | Default |
|---------|---------|---------|
| Position | Top, Center, Bottom, Full | Center |
| Scale | 50%, 80%, 100% | 80% |

---

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot & show menu |
| `/stats` | View your statistics |
| `/clean` | Clean server files |
| `/help` | Show help |
| `/cancel` | Cancel operation |

---

## 🔧 Features For Free Tier

### Auto Cleanup
- ✅ Temp files deleted after processing
- ✅ Output files deleted after sending
- ✅ Old images deleted when changing
- ✅ Server stays clean automatically

### Storage Efficient
- ✅ SQLite database (minimal space)
- ✅ Only active files stored
- ✅ Auto cleanup on startup

---

## 📁 Project Structure

```
telegram-bot/
├── main.py              # Main bot with batch processing
├── config.py            # Configuration loader
├── database.py          # User data & queue management
├── pdf_processor.py     # PDF processing module
├── helpers.py           # Utility functions
├── requirements.txt     # Dependencies
├── .env                 # Your credentials
├── bot_database.db      # SQLite database
├── user_images/         # Saved default images
├── temp/                # Temporary files (auto-cleaned)
└── output/              # Processed PDFs (auto-cleaned)
```

---

## ⚠️ Troubleshooting

### Bot not starting?
```bash
# Check .env file
cat .env

# Verify credentials are correct
```

### PDF processing errors?
- Check file is valid PDF
- File size under 50MB
- Default image is set

### Import errors?
```bash
pip install -r requirements.txt --upgrade
```

---

## 📜 License

MIT License - Free to use and modify!

---

<div align="center">

**Made with ❤️ for Telegram Bot Community**

**Perfect for Free Tier Servers!**

</div>
