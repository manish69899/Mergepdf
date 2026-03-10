"""
📄 PDF Processor Module
Merges Base PDF with Target PDFs using pypdf (Advanced, Fast & Error Free)
"""

import os
import logging
from pypdf import PdfWriter, PdfReader
from pypdf.errors import PdfReadError
from typing import Dict, Any

# Error tracking ke liye logger setup
logger = logging.getLogger(__name__)

class PDFProcessor:
    def merge_pdfs(self, target_pdf: str, base_pdf: str, position: str, output_path: str) -> Dict[str, Any]:
        """
        Merge karta hai do PDFs ko.
        position == 'start': [Base PDF] + [Target PDF]
        position == 'end': [Target PDF] + [Base PDF]
        """
        # 1. File existence check taaki unexpected crash na aaye
        if not os.path.exists(target_pdf) or not os.path.exists(base_pdf):
            return {"success": False, "error": "Base ya Target file disk par nahi mili."}

        merger = None
        try:
            merger = PdfWriter()
            
            # Using the append method handles bookmarks, metadata, and pages flawlessly
            if position == "start":
                merger.append(base_pdf)
                merger.append(target_pdf)
            else: # position == "end"
                merger.append(target_pdf)
                merger.append(base_pdf)
                
            # Output file safely likhna
            with open(output_path, "wb") as f:
                merger.write(f)
                
            return {"success": True, "output_path": output_path}
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            return {"success": False, "error": str(e)}
        finally:
            # RAM free karne ke liye merger safely close karna zaruri hai
            if merger:
                merger.close()

    def is_valid_pdf(self, pdf_path: str) -> bool:
        """
        Fast check karega ki file asli PDF hai, corrupt nahi hai, 
        aur password protected nahi hai.
        """
        if not os.path.exists(pdf_path):
            return False
            
        try:
            # Fast Check: Sirf PdfReader se read karna zyada fast hai bajaay append karne ke
            reader = PdfReader(pdf_path)
            
            # Agar password protected hai, toh bot usko merge nahi kar payega
            if reader.is_encrypted:
                logger.warning(f"Encrypted/Locked PDF detected: {pdf_path}")
                return False
                
            # Ek page access karke try karte hain corruption check karne ke liye
            if len(reader.pages) > 0:
                _ = reader.pages[0]
            
            return True
            
        except PdfReadError:
            # Agar file bilkul hi ajeeb/corrupt format me hai
            logger.warning(f"Corrupt or Invalid PDF detected: {pdf_path}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while validating PDF {pdf_path}: {e}")
            return False

# Global instance create karke export kar diya
pdf_processor = PDFProcessor()