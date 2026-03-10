"""
🔧 Configuration Module
Loads all settings from .env file with Absolute Paths & Safe Parsing
Includes Auto-Cleanup logic for server storage management
"""

import os
import shutil
import logging
from dotenv import load_dotenv
from typing import List

# Logger setup
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Absolute Base Directory taaki FileNotFoundError kabhi na aaye
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Bot Configuration Class"""
    
    def __init__(self):
        # 1. Telegram API Credentials
        try:
            self.API_ID: int = int(os.getenv("API_ID", "0"))
        except ValueError:
            self.API_ID = 0  
            
        self.API_HASH: str = os.getenv("API_HASH", "")
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        
        # 2. Admin System
        admin_str = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS: List[int] = [
            int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()
        ]
        
        # 3. Bot Settings
        self.BOT_NAME: str = os.getenv("BOT_NAME", "PDF_Master_Pro")
        self.BOT_VERSION: str = os.getenv("BOT_VERSION", "2.0.0")
        
        # 4. Absolute Paths
        self.TEMP_DIR: str = os.path.join(BASE_DIR, "temp")
        self.OUTPUT_DIR: str = os.path.join(BASE_DIR, "output")
        self.USER_BASE_DIR: str = os.path.join(BASE_DIR, "user_base_pdfs")
        self.DATABASE_PATH: str = os.path.join(BASE_DIR, os.getenv("DATABASE_PATH", "bot_database.db"))
        
        # 5. Image Settings
        self.DEFAULT_IMAGE_PATH: str = os.path.join(BASE_DIR, os.getenv("DEFAULT_IMAGE_PATH", "assets/default_cover.png").lstrip("./"))
        try:
            self.IMAGE_QUALITY: int = int(os.getenv("IMAGE_QUALITY", "95"))
        except ValueError:
            self.IMAGE_QUALITY = 95
        
        # 6. PDF & Storage Settings
        try:
            self.MAX_PDF_SIZE_MB: int = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
        except ValueError:
            self.MAX_PDF_SIZE_MB = 50
            
        self.MAX_PDF_SIZE_BYTES: int = self.MAX_PDF_SIZE_MB * 1024 * 1024
        
        # 7. Auto Cleanup (Server Storage Protection)
        self.AUTO_CLEANUP: bool = str(os.getenv("AUTO_CLEANUP", "true")).lower() == "true"
        try:
            self.MAX_STORAGE_MB: int = int(os.getenv("MAX_STORAGE_MB", "500"))
        except ValueError:
            self.MAX_STORAGE_MB = 500
        
        # 8. Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
    def validate(self) -> bool:
        """Validate required configuration before starting bot"""
        errors = []
        if not self.API_ID: 
            errors.append("❌ API_ID is missing or invalid! Kripya .env file check karein.")
        if not self.API_HASH: 
            errors.append("❌ API_HASH is missing! Kripya .env file check karein.")
        if not self.BOT_TOKEN: 
            errors.append("❌ BOT_TOKEN is missing! Kripya .env file check karein.")
            
        if errors:
            logger.error("🚨 Configuration Errors:")
            for error in errors: logger.error(f"   {error}")
            return False
        return True
    
    def create_directories(self):
        """Auto Create necessary directories"""
        for directory in [self.TEMP_DIR, self.OUTPUT_DIR, self.USER_BASE_DIR]:
            os.makedirs(directory, exist_ok=True)
            
        # Assets folder for default image if it doesn't exist
        assets_dir = os.path.dirname(self.DEFAULT_IMAGE_PATH)
        if assets_dir:
            os.makedirs(assets_dir, exist_ok=True)

    def get_dir_size_mb(self, directory: str) -> float:
        """Calculates total size of a directory in MB"""
        total_size = 0
        if os.path.exists(directory):
            for dirpath, _, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024)

    def run_auto_cleanup(self):
        """Checks storage limits and cleans temp/output folders if needed"""
        if not self.AUTO_CLEANUP:
            return
            
        temp_size = self.get_dir_size_mb(self.TEMP_DIR)
        out_size = self.get_dir_size_mb(self.OUTPUT_DIR)
        total_used = temp_size + out_size
        
        # Agar limit 80% se upar chali gayi (e.g., 400MB out of 500MB)
        limit_threshold = self.MAX_STORAGE_MB * 0.8 
        
        if total_used > limit_threshold:
            logger.warning(f"🚨 Storage Reached {total_used:.2f}MB! Running Auto-Cleanup...")
            try:
                # Sirf temp aur output delete karenge, users ke Base PDFs nahi!
                shutil.rmtree(self.TEMP_DIR, ignore_errors=True)
                shutil.rmtree(self.OUTPUT_DIR, ignore_errors=True)
                self.create_directories() # Folders wapas bana do
                logger.info("✅ Auto-Cleanup Successful. Server space freed.")
            except Exception as e:
                logger.error(f"❌ Auto-Cleanup failed: {e}")

# Global configuration instance
config = Config()