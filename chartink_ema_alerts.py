import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import logging
import time
import html
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for GCP Cloud Logging compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# Load credentials from environment variables
# Strip whitespace, quotes, newlines, and any extra characters from environment variables
def clean_env_var(value):
    """Clean environment variable by removing quotes, whitespace, and control characters"""
    if not value:
        return ""
    # Strip whitespace and common quote characters
    cleaned = value.strip().strip('"').strip("'").strip('`').strip()
    # Remove any control characters (newlines, carriage returns, tabs, etc.)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char == '\n')
    # Remove newlines specifically
    cleaned = cleaned.replace('\n', '').replace('\r', '').replace('\t', '')
    return cleaned.strip()

TELEGRAM_BOT_TOKEN = clean_env_var(os.environ.get("TELEGRAM_BOT_TOKEN", ""))
TELEGRAM_CHAT_ID = clean_env_var(os.environ.get("TELEGRAM_CHAT_ID", ""))

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment variables or .env file")

logger.info(f"Bot token length: {len(TELEGRAM_BOT_TOKEN)}, Chat ID: {TELEGRAM_CHAT_ID}")

STATE_FILE = os.environ.get("STATE_FILE", "state.json")
STATE_RETENTION_DAYS = 7  # Clear symbols older than this

# Market hours configuration (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 20
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 25

# NSE Trading Holidays for 2026
NSE_HOLIDAYS_2026 = [
    datetime(2026, 1, 26, tzinfo=IST),   # Republic Day
    datetime(2026, 3, 3, tzinfo=IST),    # Holi
    datetime(2026, 3, 26, tzinfo=IST),   # Shri Ram Navami
    datetime(2026, 3, 31, tzinfo=IST),   # Shri Mahavir Jayanti
    datetime(2026, 4, 3, tzinfo=IST),    # Good Friday
    datetime(2026, 4, 14, tzinfo=IST),   # Dr. Baba Saheb Ambedkar Jayanti
    datetime(2026, 5, 1, tzinfo=IST),    # Maharashtra Day
    datetime(2026, 5, 28, tzinfo=IST),   # Bakri Id
    datetime(2026, 6, 26, tzinfo=IST),   # Muharram
    datetime(2026, 9, 14, tzinfo=IST),   # Ganesh Chaturthi
    datetime(2026, 10, 2, tzinfo=IST),   # Mahatma Gandhi Jayanti
    datetime(2026, 10, 20, tzinfo=IST),  # Dussehra
    datetime(2026, 11, 10, tzinfo=IST),  # Diwali-Balipratipada
    datetime(2026, 11, 24, tzinfo=IST),  # Prakash Gurpurb Sri Guru Nanak Dev
    datetime(2026, 12, 25, tzinfo=IST),  # Christmas
]

SCREENS = {
    "EMA20_TOUCH": {
        "url": "https://chartink.com/screener/stocks-are-touching-20-day-ema-and-reversing",
        "label": "EMA20 Touch Alert"
    },
    "EMA20_REVERSAL": {
        "url": "https://chartink.com/screener/stocks-reversing-from-20-day-ema",
        "label": "EMA20 Reversal Alert"
    },
    "EMA50_TOUCH": {
        "url": "https://chartink.com/screener/stocks-are-touching-50-day-ema-and-reversing-2",
        "label": "EMA50 Touch Alert"
    },
    "EMA50_REVERSAL": {
        "url": "https://chartink.com/screener/stocks-reversing-from-50-day-ema",
        "label": "EMA50 Reversal Alert"
    },
    "EMA200_TOUCH": {
        "url": "https://chartink.com/screener/stocks-are-touching-200-day-ema-and-reversing",
        "label": "EMA200 Touch Alert"
    },
    "EMA200_REVERSAL": {
        "url": "https://chartink.com/screener/stocks-reversing-from-200-day-ema",
        "label": "EMA200 Reversal Alert"
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# ---------- MARKET HOURS ----------
def is_market_open():
    """Check if NSE market is currently open"""
    now = datetime.now(IST)

    # Check if it's a weekday (Monday=0, Sunday=6)
    if now.weekday() >= 5:  # Saturday or Sunday
        logger.info(f"Market closed: Weekend ({now.strftime('%A')})")
        return False

    # Check if it's a trading holiday
    today = now.date()
    for holiday in NSE_HOLIDAYS_2026:
        if holiday.date() == today:
            logger.info(f"Market closed: NSE Trading Holiday ({holiday.strftime('%d-%b-%Y')})")
            return False

    # Check if within market hours (9:20 AM to 3:25 PM IST)
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)

    if now < market_open:
        logger.info(f"Market closed: Before market hours (opens at {market_open.strftime('%H:%M')})")
        return False

    if now > market_close:
        logger.info(f"Market closed: After market hours (closed at {market_close.strftime('%H:%M')})")
        return False

    # Market is open
    logger.info(f"Market is open - Current time: {now.strftime('%H:%M:%S')}")
    return True


def is_last_run_of_day():
    """Check if this is the last run of the day (3:25 PM)"""
    now = datetime.now(IST)
    # Check if current time is at or after 3:25 PM (market close time)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    return now >= market_close


# ---------- STATE ----------
def load_state():
    """Load state with timestamp tracking"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse state file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
    return {}


def save_state(state):
    """Save state with error handling"""
    try:
        # Check if this is the last run of the day
        if is_last_run_of_day():
            logger.info("🧹 Last run of the day - Clearing state for fresh start tomorrow")
            # Save empty state to clear all entries
            with open(STATE_FILE, "w") as f:
                json.dump({}, f, indent=2)
            logger.info("State cleared successfully - Ready for next trading day")
        else:
            # Normal save with current state
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            logger.info("State saved successfully")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def clean_old_entries(state):
    """Remove entries older than STATE_RETENTION_DAYS"""
    current_time = datetime.now(IST)
    cutoff_time = current_time - timedelta(days=STATE_RETENTION_DAYS)

    for ema in state:
        if isinstance(state[ema], dict):
            # Remove old timestamp entries
            state[ema] = {
                symbol: timestamp
                for symbol, timestamp in state[ema].items()
                if datetime.fromisoformat(timestamp) > cutoff_time
            }
        elif isinstance(state[ema], list):
            # Migrate old format to new format with timestamps
            logger.info(f"Migrating {ema} state to new format")
            state[ema] = {}

    return state


# ---------- TELEGRAM ----------
def send_telegram(msg):
    """Send message to Telegram with retry logic"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result}")

        except requests.exceptions.Timeout:
            logger.warning(f"Telegram request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            error_detail = ""
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = f" - Response: {e.response.text}"
            except:
                pass
            logger.error(f"Telegram request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}{error_detail}")
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    logger.error("Failed to send Telegram message after all retries")
    return False


# ---------- SCRAPER ----------
def fetch_symbols(url):
    """Fetch symbols from Chartink with retry logic using Playwright"""
    for attempt in range(MAX_RETRIES):
        browser = None
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=HEADERS["User-Agent"],
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                logger.info(f"Loading page: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for the page to fully load - try multiple selectors
                logger.info("Waiting for data to load...")
                time.sleep(5)  # Give time for JavaScript to execute

                # Try to wait for table with tbody
                try:
                    page.wait_for_selector("table tbody tr", timeout=10000)
                    logger.info("Table with rows found")
                except PlaywrightTimeout:
                    logger.info("Specific selector timeout, checking if table exists anyway...")

                # Get the page content after JavaScript has executed
                html_content = page.content()
                browser.close()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, "lxml")
                tables = soup.find_all("table")

                results = []
                if not tables:
                    logger.warning(f"No tables found on page: {url}")
                    return results

                logger.info(f"Found {len(tables)} tables, checking for data...")

                # Check all tables to find one with stock data
                for table_idx, table in enumerate(tables):
                    tbody = table.find("tbody")
                    if not tbody:
                        continue

                    rows = tbody.find_all("tr")
                    if len(rows) == 0:
                        continue

                    logger.info(f"Table {table_idx + 1} has {len(rows)} rows, attempting to parse...")

                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) < 6:  # Need at least 6 columns for Chartink format
                            continue

                        # Extract data from Chartink table
                        # Format: [Index, Name, Symbol, Type, Percentage, Price, Volume, ...]
                        try:
                            symbol = cols[2].get_text(strip=True)  # Column 2: Symbol
                            name = cols[1].get_text(strip=True)    # Column 1: Name
                            pct = cols[4].get_text(strip=True)     # Column 4: Percentage
                            price = cols[5].get_text(strip=True)   # Column 5: Price

                            # Filter out ETFs and validate symbol
                            if symbol and len(symbol) > 1 and not symbol.isdigit():
                                # Check if "ETF" appears in the name (case insensitive)
                                if "ETF" in name.upper():
                                    logger.debug(f"Filtered out ETF: {symbol} ({name})")
                                    continue

                                results.append({
                                    "symbol": symbol,
                                    "price": price,
                                    "pct": pct
                                })
                        except Exception as e:
                            logger.debug(f"Failed to parse row: {e}")
                            continue

                    # If we found results in this table, stop checking other tables
                    if results:
                        logger.info(f"Fetched {len(results)} symbols from table {table_idx + 1}")
                        return results

                if not results:
                    logger.warning(f"No valid stock data found in any table")

                return results

        except PlaywrightTimeout as e:
            logger.warning(f"Playwright timeout (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching symbols (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass

        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

    logger.error(f"Failed to fetch symbols after all retries: {url}")
    return []


# ---------- MAIN ----------
def main():
    """Main execution function with error handling and state management"""
    logger.info("=== Starting EMA Retest Alert Script ===")

    # Check if market is open
    if not is_market_open():
        logger.info("Script execution skipped - Market is closed")
        return


    try:
        now = datetime.now(IST).strftime("%H:%M")
        current_timestamp = datetime.now(IST).isoformat()

        state = load_state()
        state = clean_old_entries(state)

        total_new_alerts = 0

        # Group screens by EMA type (EMA20, EMA50, EMA200)
        ema_groups = {
            "EMA20": ["EMA20_TOUCH", "EMA20_REVERSAL"],
            "EMA50": ["EMA50_TOUCH", "EMA50_REVERSAL"],
            "EMA200": ["EMA200_TOUCH", "EMA200_REVERSAL"]
        }

        for ema_name, screen_keys in ema_groups.items():
            logger.info(f"Processing {ema_name} alerts (Touch + Reversal)...")

            # Collect alerts for both touch and reversal
            touch_alerts = []
            reversal_alerts = []

            for screen_key in screen_keys:
                ema_config = SCREENS[screen_key]
                ema_label = ema_config["label"]
                ema_url = ema_config["url"]

                logger.info(f"  Fetching {ema_label}...")

                try:
                    stocks = fetch_symbols(ema_url)
                except Exception as e:
                    logger.error(f"{ema_label} fetch failed: {e}", exc_info=True)
                    continue

                # Initialize state with dict format if needed
                if screen_key not in state:
                    state[screen_key] = {}
                elif isinstance(state[screen_key], list):
                    state[screen_key] = {}

                # Find new entries
                new_entries = []
                for s in stocks:
                    if s["symbol"] not in state[screen_key]:
                        new_entries.append(s)
                        state[screen_key][s["symbol"]] = current_timestamp
                        logger.info(f"  New alert: {ema_label} - {s['symbol']}")

                # Categorize by touch or reversal
                if "TOUCH" in screen_key:
                    touch_alerts = new_entries
                elif "REVERSAL" in screen_key:
                    reversal_alerts = new_entries

            # Send combined message if there are any alerts for this EMA
            if touch_alerts or reversal_alerts:
                msg = f"📊 <b>{html.escape(ema_name)} Alerts</b>\n🕒 {html.escape(str(now))}\n\n"

                if touch_alerts:
                    msg += f"<b>🔵 Touch Alert</b>\n"
                    for s in touch_alerts:
                        symbol = html.escape(str(s['symbol']))
                        price = html.escape(str(s['price']))
                        pct = html.escape(str(s['pct']))
                        msg += f"  <b>{symbol}</b> | ₹{price} | {pct}\n"
                    msg += "\n"

                if reversal_alerts:
                    msg += f"<b>🟢 Reversal Alert</b>\n"
                    for s in reversal_alerts:
                        symbol = html.escape(str(s['symbol']))
                        price = html.escape(str(s['price']))
                        pct = html.escape(str(s['pct']))
                        msg += f"  <b>{symbol}</b> | ₹{price} | {pct}\n"

                if send_telegram(msg):
                    alert_count = len(touch_alerts) + len(reversal_alerts)
                    total_new_alerts += alert_count
                    logger.info(f"Sent {alert_count} alerts for {ema_name} (Touch: {len(touch_alerts)}, Reversal: {len(reversal_alerts)})")
            else:
                logger.info(f"No new alerts for {ema_name}")

        save_state(state)
        logger.info(f"=== Script completed. Total new alerts: {total_new_alerts} ===")

    except Exception as e:
        logger.error(f"Critical error in main execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Check if running in Cloud Run (has PORT environment variable)
    port = os.environ.get("PORT")

    if port:
        # Running in Cloud Run - start HTTP server
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                """Handle GET requests - run the main script"""
                try:
                    # Run the main script
                    main()

                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'EMA Alerts script executed successfully\n')
                except Exception as e:
                    # Send error response
                    logger.error(f"Error in HTTP handler: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: {str(e)}\n'.encode())

            def log_message(self, format, *args):
                """Override to use our logger instead of stderr"""
                logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

        # Start HTTP server
        server = HTTPServer(('0.0.0.0', int(port)), HealthCheckHandler)
        logger.info(f"Starting HTTP server on port {port}")
        server.serve_forever()
    else:
        # Running locally - just execute once
        main()

