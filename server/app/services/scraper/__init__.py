import os
import re
import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
from datetime import datetime
import json

from app.services.google_sheets import sheets_service

def human_delay(a=1.0, b=2.0):
    total_sleep = random.uniform(a, b)
    intervals = int(total_sleep / 0.2)
    for _ in range(intervals):
        from app.services import scraper as scraper_module
        if scraper_module.current_scraper and scraper_module.current_scraper.should_stop:
            return
        time.sleep(0.2)
    time.sleep(total_sleep % 0.2)

def clean_text(text):
    return (text or "").strip()

def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text or "")))

def extract_phones(text):
    return list(set(re.findall(r"\+?\d[\d -]{8,12}\d", text or "")))

# In-memory logging queue for SSE/WebSockets to consume
scrape_logs = []
current_scraper = None

def log_msg(msg: str):
    print(msg)
    timestamp = datetime.now().strftime("%H:%M:%S")
    scrape_logs.append(f"[{timestamp}] {msg}")

class GMBScraper:
    def __init__(self, keywords_str: str, relevance_keywords_str: str, city: str, country: str, limit: int):
        # Parse inputs
        self.keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        
        loc_parts = []
        if city: loc_parts.append(city.strip())
        if country: loc_parts.append(country.strip())
        self.locations = [", ".join(loc_parts)] if loc_parts else [""]
        
        self.limit = limit
        self.headless = True # Enforce headless for backend
        self.should_stop = False
        
        # Relevance - can be customized later
        self.relevance_keywords = [k.strip() for k in relevance_keywords_str.split(",") if k.strip()]
        self.decision_makers = ["Advisor", "Coordinator", "Lead", "President", "Secretary", "Head", "Director", "Principal"]

    def is_relevant(self, text):
        if not self.relevance_keywords:
            return True
        text_lower = text.lower()
        for k in self.relevance_keywords:
            pattern = r'\b' + re.escape(k.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return True
        return False

    def find_decision_makers(self, text):
        found = []
        lines = text.split('\n')
        for line in lines:
            for title in self.decision_makers:
                if title.lower() in line.lower() and len(line.strip()) < 100:
                    found.append(line.strip())
        return list(set(found))

    def deep_scrape_website(self, context, url):
        log_msg(f"   → Deep scraping: {url}")
        meta = {
            "emails": [], 
            "phones": [], 
            "decision_makers": [], 
            "relevant": len(self.relevance_keywords) == 0
        }
        
        try:
            page = context.new_page()
            page.goto(url, timeout=15000)
            human_delay(2, 3)
            
            content = page.content()
            text = page.inner_text("body")
            
            if self.is_relevant(text):
                meta["relevant"] = True
                
            meta["emails"].extend(extract_emails(content))
            meta["phones"].extend(extract_phones(text))
            
            # Sub-pages logic simplified for Speed in MVP
            links = page.query_selector_all("a")
            sub_pages = set()
            keywords = ["about", "contact", "team"]
            for link in links:
                href = link.get_attribute("href")
                if href and any(k in href.lower() for k in keywords):
                    full_url = urllib.parse.urljoin(url, href)
                    if url in full_url:
                        sub_pages.add(full_url)
            
            for sub_url in list(sub_pages)[:2]:
                if self.should_stop: break
                try:
                    page.goto(sub_url, timeout=10000)
                    human_delay(1, 2)
                    sub_text = page.inner_text("body")
                    meta["emails"].extend(extract_emails(page.content()))
                    meta["phones"].extend(extract_phones(sub_text))
                except Exception:
                    continue
            page.close()
        except Exception as e:
            log_msg(f"   ⚠ Error deep scraping {url}: {e}")
            
        meta["emails"] = list(set(meta["emails"]))
        meta["phones"] = list(set(meta["phones"]))
        return meta

    def run(self):
        log_msg("🚀 Starting Scraper Task...")
        
        if not sheets_service.client:
            log_msg("❌ Google Sheets not connected. Run aborted.")
            return

        try:
            sheets_service.create_or_get_sheet()
        except Exception as e:
            log_msg(f"❌ Failed to initialize Google Sheet: {e}")
            return

        all_combinations = []
        for keyword in self.keywords:
            for loc in self.locations:
                query = f"{keyword} in {loc}" if loc else keyword
                all_combinations.append(query)
                
        random.shuffle(all_combinations)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            # Overriding locale, timezone, and geolocation so Google Maps doesn't bias to the host's actual IP location
            context = browser.new_context(
                locale="en-US",
                timezone_id="America/New_York",
                geolocation={"longitude": -74.006, "latitude": 40.7128},
                permissions=["geolocation"]
            )
            
            processed_count = 0
            
            for query in all_combinations:
                if processed_count >= self.limit or self.should_stop:
                    break
                    
                log_msg(f"\n═══ Processing: {query} ═══")
                try:
                    page = context.new_page()
                    search_url = "https://www.google.com/maps/search/?q=" + urllib.parse.quote_plus(query) + "&hl=en"
                    page.goto(search_url)
                    human_delay(2, 3)
                    
                    try:
                        if page.query_selector('button[aria-label="Accept all"]'):
                            page.click('button[aria-label="Accept all"]', timeout=2000)
                    except: pass
                    
                    # Dynamic Scrolling Logic
                    previous_count = 0
                    scroll_attempts_without_new = 0
                    
                    while True:
                        if self.should_stop: break
                        
                        # Find current anchors
                        anchors = page.query_selector_all('a[href*="google.com/maps/place"]')
                        current_count = len(anchors)
                        
                        if current_count >= self.limit:
                            break # We have enough
                            
                        if current_count == previous_count:
                            scroll_attempts_without_new += 1
                        else:
                            scroll_attempts_without_new = 0 # Reset if we found new ones
                            
                        if scroll_attempts_without_new >= 5: # Give up after 5 scrolls with no new results
                            break
                            
                        previous_count = current_count
                        
                        # Try to find the scrollable container and scroll it, or just scroll window
                        page.evaluate('''() => {
                            let scrollableDiv = document.querySelector('div[role="feed"]');
                            if (scrollableDiv) {
                                scrollableDiv.scrollBy(0, 5000);
                            } else {
                                window.scrollBy(0, 5000);
                            }
                        }''')
                        human_delay(1, 2)

                    if self.should_stop: break
                    
                    anchors = page.query_selector_all('a[href*="google.com/maps/place"]')
                    hrefs = list(set([a.get_attribute("href") for a in anchors if a.get_attribute("href")]))
                    log_msg(f"Found {len(hrefs)} results initially.")
                    
                    for maps_url in hrefs:
                        if processed_count >= self.limit or self.should_stop:
                            break
                            
                        try:
                            page.goto(maps_url)
                            human_delay(1, 2)
                            
                            name = clean_text(page.inner_text('h1') if page.query_selector('h1') else "")
                            phone_el = page.query_selector('button[data-item-id^="phone:tel:"]')
                            phone = clean_text(phone_el.get_attribute("aria-label").replace("Phone:", "") if phone_el else "")
                            website_el = page.query_selector('a[data-item-id="authority"]')
                            website = website_el.get_attribute("href") if website_el else ""
                            
                            # Extract rating using a robust JS evaluation to ensure it contains a number
                            rating = page.evaluate('''() => {
                                let els = document.querySelectorAll('[aria-label*="stars"], [aria-label*="Stars"]');
                                for (let el of els) {
                                    let label = el.getAttribute('aria-label');
                                    if (label && label.match(/[0-9.]+\s*stars/i)) {
                                        return label.trim();
                                    }
                                }
                                return "";
                            }''')
                            rating = clean_text(rating)
                            
                            log_msg(f"Inspecting: {name} | {phone} | {rating}")
                            
                            extra_data = {
                                "emails": [], 
                                "relevant": len(self.relevance_keywords) == 0, # Only default True if no keywords exist
                                "phones": []
                            }
                            if website:
                                extra_data = self.deep_scrape_website(context, website)

                            if not extra_data["relevant"]:
                                log_msg("   → Skipping: Low relevance")
                                continue
                                
                            final_email = extra_data["emails"][0] if extra_data["emails"] else ""
                            final_phone = phone or (extra_data["phones"][0] if extra_data["phones"] else "")
                            
                            lead_data = {
                                "name": name,
                                "phone": final_phone,
                                "profession": query,
                                "email": final_email,
                                "website": website,
                                "query": query,
                                "address": "", # To implement later based on selector
                                "rating": rating
                            }
                            
                            if self.should_stop:
                                log_msg("   🛑 Scraping manually stopped before saving.")
                                break
                                
                            is_new = sheets_service.append_lead(lead_data)
                            if is_new:
                                log_msg("   ✅ Added to Sheet!")
                                processed_count += 1
                            else:
                                log_msg("   ⏭️ Skipped: Duplicate lead already in sheet")
                            
                        except Exception as e:
                            log_msg(f"Error on card: {e}")
                            
                    if self.should_stop:
                        page.close()
                        break
                        
                    page.close()
                except Exception as e:
                    log_msg(f"Query error: {e}")
            
            browser.close()
        log_msg(f"🎉 Done! Total scraped: {processed_count}")
        return processed_count
