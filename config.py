"""
Configuration settings for the Tashi bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN environment variable is not set")

# Website Scraping Configuration
BASE_URL = "https://breathebhutan.com"
SCRAPE_TARGETS = [
    "/",  # Homepage
    "/cultural-tours/",
    "/festivals/",
    "/trekking/",
    "/itineraries/"
]

# Data Storage Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TOURS_FILE = os.path.join(DATA_DIR, "tours.json")
FESTIVALS_FILE = os.path.join(DATA_DIR, "festivals.json")
TREKKING_FILE = os.path.join(DATA_DIR, "trekking.json")
ITINERARIES_FILE = os.path.join(DATA_DIR, "itineraries.json")

# Email Configuration for Business Integration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BREATHE_BHUTAN_EMAIL = os.getenv("BREATHE_BHUTAN_EMAIL", "contact@breathebhutan.com")

# Logging Configuration
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "tashi.log")

# Bot Response Messages
WELCOME_MESSAGE = """
Hello! I'm Tashi, your personal travel assistant for planning your trip to Bhutan.
I can help you discover cultural tours, festivals, trekking options, and create custom itineraries.
What type of travel experience are you looking for?
"""

TRIP_TYPE_PROMPT = """
What kind of experience are you looking for in Bhutan?
- Cultural Tours
- Festivals
- Trekking
- Custom Itinerary
Please select one or tell me more about what you're interested in.
"""

DURATION_PROMPT = "Great choice! How many days are you planning to stay in Bhutan?"

TRAVEL_DATE_PROMPT = "When are you planning to visit? Please provide a month or specific dates if you know them."

FINALIZATION_MESSAGE = """
Thank you for planning your trip with me! I've sent your customized itinerary to the Breathe Bhutan team.
They will contact you shortly to finalize the details and answer any questions you may have.
"""

# Error Messages
ERROR_MESSAGE = "I'm sorry, I encountered an error. Please try again or contact Breathe Bhutan directly."
CONNECTION_ERROR_MESSAGE = "I'm having trouble connecting right now. Please try again in a few moments." 