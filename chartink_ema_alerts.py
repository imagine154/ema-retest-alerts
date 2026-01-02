import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import logging
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configure logging for GCP Cloud Logging compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# Load credentials from environment variables for security (fallback to hardcoded for local testing)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1002343316074")

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
    "EMA20": "https://chartink.com/screener/stocks-are-touching-20-day-ema-and-reversing",
    "EMA50": "https://chartink.com/screener/stocks-are-touching-50-day-ema-and-reversing-2",
    "EMA200": "https://chartink.com/screener/stocks-are-touching-200-day-ema-and-reversing"
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
            logger.error(f"Telegram request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
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
                            pct = cols[4].get_text(strip=True)     # Column 4: Percentage
                            price = cols[5].get_text(strip=True)   # Column 5: Price

                            # Basic validation - symbol should be text, not empty
                            if symbol and len(symbol) > 1 and not symbol.isdigit():
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

        for ema, url in SCREENS.items():
            logger.info(f"Processing {ema} screen...")

            try:
                stocks = fetch_symbols(url)
            except Exception as e:
                logger.error(f"{ema} fetch failed: {e}", exc_info=True)
                continue

            new_entries = []

            # Initialize state with dict format if needed
            if ema not in state:
                state[ema] = {}
            elif isinstance(state[ema], list):
                # Migrate old list format to dict
                state[ema] = {}

            for s in stocks:
                if s["symbol"] not in state[ema]:
                    new_entries.append(s)
                    state[ema][s["symbol"]] = current_timestamp
                    logger.info(f"New alert: {ema} - {s['symbol']}")

            if new_entries:
                msg = f"📊 <b>{ema} Reversal Alert</b>\n🕒 {now}\n\n"
                for s in new_entries:
                    msg += f"<b>{s['symbol']}</b> | ₹{s['price']} | {s['pct']}\n"

                if send_telegram(msg):
                    total_new_alerts += len(new_entries)
                    logger.info(f"Sent {len(new_entries)} alerts for {ema}")
            else:
                logger.info(f"No new alerts for {ema}")

        save_state(state)
        logger.info(f"=== Script completed. Total new alerts: {total_new_alerts} ===")

    except Exception as e:
        logger.error(f"Critical error in main execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

