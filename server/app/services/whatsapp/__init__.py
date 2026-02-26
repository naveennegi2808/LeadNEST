import os
import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
import threading

from app.services.google_sheets import sheets_service

whatsapp_logs = []

def log_wa(msg: str):
    print(msg)
    whatsapp_logs.append(msg)

class WhatsAppService:
    def __init__(self, message_template: str, limit: int = None):
        self.message_template = message_template
        self.limit = limit
        self.user_data_dir = os.path.join(os.getcwd(), "whatsapp_session_api")
        self.is_running = False

    def clean_phone(self, s: str) -> str:
        s = str(s or "").strip()
        out = "".join(ch for ch in s if ch.isdigit() or ch == "+")
        if out.count("+") > 1:
            out = out.replace("+", "")
        if not out.startswith("+") and out:
             out = "+91" + out # default IN, configurable later
        return out

    def run_automation(self):
        if not sheets_service.client or not sheets_service.sheet_id:
             log_wa("❌ Google Sheets not connected! Cannot read leads.")
             return

        self.is_running = True
        log_wa("🚀 Starting WhatsApp Automation...")
        log_wa(f"ℹ️  Session directory: {self.user_data_dir}")
        log_wa("⚠️ A browser window will open. Scan the QR code if you aren't logged in.")

        sh = sheets_service.client.open_by_key(sheets_service.sheet_id)
        worksheet = sh.sheet1
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            log_wa("Sheet is empty or missing data.")
            self.is_running = False
            return
            
        headers = [h.strip().lower() for h in all_values[0]]
        rows = all_values[1:]
        
        try:
             idx_phone = next(i for i, h in enumerate(headers) if "phone" in h or "contact" in h)
             idx_status = next(i for i, h in enumerate(headers) if "status" in h)
        except StopIteration:
             log_wa("Could not find 'Phone' or 'Status' columns in sheet.")
             self.is_running = False
             return

        sent_count = 0
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=False, # Must be visibile for QR scan
                channel="chrome",
                args=["--start-maximized", "--no-sandbox"]
            )
            
            page = browser.pages[0]
            if not page: page = browser.new_page()
            
            page.goto("https://web.whatsapp.com/")
            log_wa("⏳ Waiting for login... please scan QR code if prompted.")
            
            try:
                page.wait_for_selector('div[id="pane-side"]', timeout=300000)
                log_wa("✅ WhatsApp Web Logged In!")
            except:
                log_wa("❌ Timeout waiting for login.")
                browser.close()
                self.is_running = False
                return

            for i, row in enumerate(rows, start=2): # +1 for 0-index, +1 for header
                if self.limit and sent_count >= self.limit:
                    log_wa(f"🛑 Reached user-defined limit of {self.limit}.")
                    break

                phone_raw = row[idx_phone] if len(row) > idx_phone else ""
                status = row[idx_status] if len(row) > idx_status else ""
                
                if status.strip().lower() not in ["new", ""]:
                    continue
                    
                phone_clean = self.clean_phone(phone_raw).lstrip('0')
                if len(phone_clean) < 10:
                    worksheet.update_cell(i, idx_status + 1, "Invalid Phone")
                    continue
                    
                log_wa(f"Sending to {phone_clean}...")
                
                try:
                     encoded_msg = urllib.parse.quote(self.message_template)
                     url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded_msg}"
                     
                     page.goto(url, wait_until='domcontentloaded', timeout=20000)
                     time.sleep(5)
                     
                     input_box_selector = '#main footer div[contenteditable="true"][role="textbox"]'
                     
                     try:
                         page.wait_for_selector(input_box_selector, timeout=15000)
                         page.locator(input_box_selector).press("Enter")
                         time.sleep(2)
                         log_wa("   ✅ Sent!")
                         worksheet.update_cell(i, idx_status + 1, "Sent")
                         sent_count += 1
                     except Exception as e:
                         # Handle invalid number popups
                         if page.query_selector('div[data-animate-modal-popup="true"]'):
                              log_wa("   ⚠️ Invalid WhatsApp Number.")
                              worksheet.update_cell(i, idx_status + 1, "Invalid WA Number")
                         else:
                              log_wa(f"   ❌ Send error: {e}")
                              worksheet.update_cell(i, idx_status + 1, "Send Error")
                except Exception as e:
                     log_wa(f"   ❌ Network/Navigation Error: {e}")
                     worksheet.update_cell(i, idx_status + 1, "Nav Error")

                time.sleep(random.randint(4, 8))

            log_wa(f"🎉 Complete. Sent {sent_count} messages.")
            time.sleep(3)
            browser.close()
            
        self.is_running = False

    def start_in_background(self):
        thread = threading.Thread(target=self.run_automation)
        thread.start()
