import os
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# Define the scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

class GoogleSheetsService:
    def __init__(self):
        self.creds = None
        self.client = None
        self.sheet_id = None
        self.existing_phones = set()
        self.existing_names = set()
        
        if os.path.exists("token.json"):
            try:
                self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
                self.client = gspread.authorize(self.creds)
            except Exception as e:
                print(f"Error loading saved token: {e}")

    def is_authenticated(self) -> bool:
        return self.client is not None

    def get_auth_url(self):
        # We need a client_secrets.json file downloaded from Google Cloud Console
        # For the demo to run without the user explicitly creating it immediately, 
        # we'll mock the URL generation if the file isn't present, or provide instructions.
        client_secrets_file = "client_secret.json"
        
        if not os.path.exists(client_secrets_file):
            return "http://localhost:3000/setup-google-oauth" # Redirect to an instruction page

        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/auth/callback' # Backend callback
        )

        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    def handle_callback(self, code: str):
         client_secrets_file = "client_secret.json"
         if not os.path.exists(client_secrets_file):
             raise Exception("client_secret.json not found")

         flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/auth/callback'
         )
         flow.fetch_token(code=code)
         self.creds = flow.credentials
         self.client = gspread.authorize(self.creds)
         
         # Save the credentials for the next run
         with open("token.json", "w") as token:
             token.write(self.creds.to_json())
             
         return True

    def create_or_get_sheet(self, sheet_name="GMB Scraper Results"):
        if not self.client:
            raise Exception("User not authenticated with Google")
            
        try:
             # Try to find existing
             sh = self.client.open(sheet_name)
             worksheet = sh.sheet1
             # Cache existing records for deduplication
             records = worksheet.get_all_records()
             self.existing_phones = {str(r.get('Phone', '')).strip() for r in records if str(r.get('Phone', '')).strip()}
             self.existing_names = {str(r.get('Name', '')).strip().lower() for r in records if str(r.get('Name', '')).strip()}
        except gspread.exceptions.SpreadsheetNotFound:
             # Create new
             sh = self.client.create(sheet_name)
             # Basic headers
             worksheet = sh.sheet1
             worksheet.update('A1:I1', [['Name', 'Phone', 'Profession', 'Status', 'Email', 'Website', 'Address', 'Query', 'Rating']])
             self.existing_phones = set()
             self.existing_names = set()
             
        self.sheet_id = sh.id
        return sh.url

    def append_lead(self, lead_data: dict):
        if not self.client or not self.sheet_id:
            raise Exception("Sheet not connected")
            
        phone = lead_data.get("phone", "").strip()
        name = lead_data.get("name", "").strip()
        
        if phone and phone in self.existing_phones:
            return False
        if name and name.lower() in self.existing_names:
            return False
            
        sh = self.client.open_by_key(self.sheet_id)
        worksheet = sh.sheet1
        
        row = [
            name,
            phone,
            lead_data.get("profession", ""),
            "New",
            lead_data.get("email", ""),
            lead_data.get("website", ""),
            lead_data.get("address", ""),
            lead_data.get("query", ""),
            lead_data.get("rating", "")
        ]
        
        # Simple append
        worksheet.append_row(row)
        
        if phone: self.existing_phones.add(phone)
        if name: self.existing_names.add(name.lower())
        return True

    def get_lead_count(self, sheet_name="GMB Scraper Results") -> int:
        import time
        if not self.client:
            return 0
            
        current_time = time.time()
        # Cache the count for 10 seconds to avoid 429 quota errors
        if hasattr(self, 'cached_lead_count') and hasattr(self, 'last_count_refresh'):
            if current_time - self.last_count_refresh < 10:
                return self.cached_lead_count
                
        try:
             sh = self.client.open(sheet_name)
             worksheet = sh.sheet1
             records = worksheet.get_all_values()
             count = max(0, len(records) - 1)
             
             self.cached_lead_count = count
             self.last_count_refresh = current_time
             return count
        except Exception as e:
             if "429" in str(e):
                 # If rate limited, return the cached count if we have one
                 return getattr(self, 'cached_lead_count', 0)
             return 0

# Instantiate a singleton for this MVP (note: this only supports 1 user at a time)
sheets_service = GoogleSheetsService()
