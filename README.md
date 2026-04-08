# Free Food Scraper

Automatically scrape IE Connects events with food and add them to Google Calendar.

## Features

- Login to IE Connects via Shibboleth authentication
- Scrape all upcoming events from the event list
- Filter events that have food (food icon detection)
- Extract event details: title, date, location
- Automatically add events to Google Calendar
- Track visited events to avoid duplicates

## Requirements

- Python 3.7+
- Chrome browser (with matching ChromeDriver)
- Google Calendar API credentials
- IE Connects account (email and password)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/salomeshioshvili/food-radar.git
cd food-radar
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Calendar API**:
   - Go to **APIs & Services** → **Library**
   - Search for "Google Calendar API"
   - Click **Enable**
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client ID**
   - Choose **Desktop application**
   - Download the JSON file
   - Rename it to `credentials.json` and place in project root
5. First run will open a browser to authorize access (creates `token.pickle` automatically)

### 4. Create `.env` file

Create a `.env` file in the project root:

```
IE_EMAIL=your-ie-email@ie.edu
IE_PASSWORD=your-ie-password
```

### 5. Download ChromeDriver

Download ChromeDriver matching your Chrome version:
[Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)

Place it in your PATH or update the script to point to it.

## Usage

```bash
python main.py
```

The script will:
1. Authenticate with IE Connects (Shibboleth login)
2. Navigate to events page and scroll through all upcoming events
3. Check each event for food indicators
4. Extract: title, date, location
5. Add food events to Google Calendar
6. Save results to `food_events.txt`
7. Track visited events in `visited.txt` to avoid re-checking

## Output

Results are saved to `food_events.txt` with format:

```
YYYY-MM-DD | Event Title | Location | calendar: True/False | URL
```

Example:
```
2026-04-24 | Family Business, Global Pay - A Conversation With Alessandro Folio |  | calendar: True | https://ieconnects.ie.edu/rsvp_boot?id=300385462
2026-04-09 | Italian Aperitivo: The Ultimate Card Competition |  | calendar: True | https://ieconnects.ie.edu/rsvp_boot?id=300385424
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | Main scraper script |
| `requirements.txt` | Python dependencies |
| `.env` | Your credentials (⚠️ never commit) |
| `credentials.json` | Google OAuth credentials (⚠️ never commit) |
| `token.pickle` | Google auth token (auto-generated) |
| `visited.txt` | Tracks checked event URLs (auto-generated) |
| `food_events.txt` | Output with found food events |
| `.gitignore` | Ignore sensitive files |

## How it Works

1. **Login**: Uses Shibboleth authentication with your IE credentials
2. **Scrape**: Collects all event URLs from IE Connects
3. **Filter**: Checks each event for food icon (`span.mdi-food`)
4. **Extract**: Parses title, date (from month/day), and location
5. **Calendar**: Adds all-day events to Google Calendar
6. **Track**: Records visited URLs to avoid duplicates

## Important Notes

**Never commit these files** (protected by `.gitignore`):
- `.env` - Contains your IE credentials
- `credentials.json` - Google OAuth secrets
- `token.pickle` - Authentication token
- `visited.txt` - Your personal event history

## Troubleshooting

- **"Yes button not found"**: The Microsoft login confirmation dialog might have a different selector. Script continues anyway.
- **Chrome not found**: Make sure Chrome is installed and ChromeDriver is in PATH
- **Google Calendar auth fails**: Delete `token.pickle` and run again to re-authenticate
- **No events found**: Check that you're logged in and events exist on IE Connects