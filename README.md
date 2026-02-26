# LeadNEST GMB Scraper & WhatsApp Automation

A modern, standalone web application that allows users to dynamically connect their own Google Sheets, scrape Google Maps leads based on specific keywords/locations, and automatically follow up with them via WhatsApp Web.

## Prerequisites
- Python 3.10+
- Node.js 18+
- Google Chrome installed

## Project Structure
- `/client`: Next.js frontend (React + Tailwind CSS)
- `/server`: FastAPI backend (Playwright for scraping & WhatsApp, Gspread for Google Sheets)

---

## Step 1: Set up Google OAuth 2.0 Credentials (Mandatory)
To allow the app to create and write to your *own* Google Sheet, you need to create a Google Cloud Project and get OAuth credentials.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **New Project** (e.g., "Scraper").
3. Go to **APIs & Services > Library**.
   - Search for **Google Sheets API** and click **Enable**.
   - Search for **Google Drive API** and click **Enable**.
4. Go to **APIs & Services > OAuth consent screen**.
   - Select **External** and click **Create**.
   - Fill in the required fields (App name, User support email, Developer contact email).
   - Under **Scopes**, you do not strictly need to add any here for testing, just Save and Continue.
   - Add your own Google email address as a **Test User** (very important!).
   - Save and Continue.
5. Go to **APIs & Services > Credentials**.
   - Click **Create Credentials** > **OAuth client ID**.
   - Application type: **Web application**.
   - Name: "Scraper App Local"
   - **Authorized redirect URIs**: Add `http://localhost:8000/api/auth/callback`
   - Click **Create**.
6. A popup will appear with your Client ID and Secret. Click **Download JSON** (it looks like `client_secret_XXXXXX.json`).
7. Rename the downloaded file to exactly **`client_secret.json`** and place it inside the `/server` folder of this project.

---

## Step 2: Backend Setup (Python / FastAPI)

1. Open a terminal and navigate to the backend folder:
   ```bash
   cd server
   ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate   # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn playwright gspread google-auth google-auth-oauthlib google-auth-httplib2 python-dotenv
   ```
4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The backend is now running at http://localhost:8000*

---

## Step 3: Frontend Setup (Next.js)

1. Open a **new** terminal window and navigate to the frontend folder:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
   *(We are adding lucide-react for icons, framer-motion for animations)*
   ```bash
   npm install lucide-react framer-motion axios swr
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *The frontend is now running at http://localhost:3000*

---

## Step 4: Using the Application

1. Open your browser and go to `http://localhost:3000`
2. **Connect Google Sheets:** Click the 'Connect' button. It will open a Google Login page. Log in with the account you added as a Test User. It will warn you the app isn't verified (click Advanced -> Go to App).
3. **Configure & Scrape:** Enter your keywords, city, and limits in the Scraper tab. Click Start. Watch the live logs. Leads will appear in a newly created spreadsheet called "GMB Scraper Results" in your Google Drive.
4. **WhatsApp Automation:** Switch to the WhatsApp tab. Enter your template, click Start. A browser window will open. **Scan the QR code**. Once logged in, the automation will pick up the "New" leads from the sheet and send messages.
