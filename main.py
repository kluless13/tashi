"""
Main entry point for the Tashi bot application.
"""
import os
import argparse
import signal
import sys
import asyncio

from utils.logger import get_logger
from bot.bot import TashiBot
from scraper.scraper import BhutanScraper
from scraper.direct_scraper import DirectBhutanScraper

logger = get_logger("main")

def handle_sigterm(signum, frame):
    """
    Handle SIGTERM signal (graceful shutdown).
    """
    logger.info("Received SIGTERM signal. Shutting down...")
    sys.exit(0)

def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Tashi - Breathe Bhutan Travel Agent Bot")
    
    # Define subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scraper command
    scraper_parser = subparsers.add_parser("scrape", help="Run the web scraper")
    scraper_parser.add_argument("--direct", action="store_true", help="Use direct content extraction instead of web scraping")
    
    # Bot command
    bot_parser = subparsers.add_parser("bot", help="Run the Telegram bot")
    bot_parser.add_argument("--webhook", help="Webhook URL for the bot")
    bot_parser.add_argument("--state-file", help="Path to state file for persistence")
    
    # Parse the arguments
    return parser.parse_args()

async def run_scraper_async():
    """
    Run the web scraper asynchronously.
    """
    logger.info("Starting scraper")
    
    try:
        scraper = BhutanScraper()
        await scraper.run_scraper()
        logger.info("Scraper completed successfully")
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")
        sys.exit(1)

def run_direct_scraper():
    """
    Run the direct scraper that extracts content without web requests.
    """
    logger.info("Starting direct content extraction")
    
    try:
        scraper = DirectBhutanScraper()
        scraper.run()
        logger.info("Direct scraper completed successfully")
    except Exception as e:
        logger.error(f"Error running direct scraper: {str(e)}")
        sys.exit(1)

def run_scraper(use_direct=False):
    """
    Run the web scraper.
    
    Args:
        use_direct (bool): Whether to use direct content extraction instead of web scraping
    """
    if use_direct:
        run_direct_scraper()
    else:
        # Run the async function in the event loop
        asyncio.run(run_scraper_async())

def run_bot(webhook_url=None, state_file=None):
    """
    Run the Telegram bot.
    
    Args:
        webhook_url (str): Webhook URL for the bot
        state_file (str): Path to state file for persistence
    """
    logger.info("Starting bot")
    
    try:
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        # Create the bot
        bot = TashiBot()
        
        # Load state if specified
        if state_file and os.path.exists(state_file):
            bot.load_state(state_file)
        
        # Set webhook if specified, otherwise use polling
        if webhook_url:
            bot.set_webhook(webhook_url)
        else:
            # Start polling
            bot.start()
        
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        sys.exit(1)

def main():
    """
    Main entry point for the application.
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run the appropriate command
    if args.command == "scrape":
        run_scraper(use_direct=args.direct)
    elif args.command == "bot":
        run_bot(args.webhook, args.state_file)
    else:
        # Default to running the bot
        run_bot()

if __name__ == "__main__":
    main() 