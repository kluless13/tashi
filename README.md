# Tashi - Breathe Bhutan Travel Agent Bot

A Telegram bot that functions as a personalized travel agent for Breathe Bhutan, providing customized travel plans based on user preferences and pre-scraped data.

## Project Overview

Tashi is a conversational Telegram bot that helps users plan their trips to Bhutan by:
- Collecting user preferences (trip type, duration, travel dates)
- Recommending customized itineraries based on pre-scraped data
- Finalizing travel plans and forwarding them to the Breathe Bhutan team

## Features

- **Data Collection**: Scrapes and stores tourism data from Breathe Bhutan website
- **Conversational Interface**: Natural language interaction through Telegram
- **Personalized Recommendations**: Custom travel plans based on user preferences
- **Business Integration**: Forwards finalized plans to the Breathe Bhutan team for follow-up

## Project Structure

```
tashi/
├── data/                   # Scraped data storage
├── scraper/                # Web scraping module
│   ├── __init__.py
│   ├── scraper.py          # Main scraping functionality
│   └── parsers/            # Content-specific parsers
├── bot/                    # Telegram bot module
│   ├── __init__.py
│   ├── bot.py              # Main bot functionality
│   ├── handlers.py         # Message handlers
│   └── conversation.py     # Conversation flow management
├── storage/                # Data storage and retrieval
│   ├── __init__.py
│   └── data_manager.py     # Data access layer
├── recommendation/         # Recommendation engine
│   ├── __init__.py
│   └── engine.py           # Matching and filtering logic
├── integration/            # Business integration module
│   ├── __init__.py
│   └── notifier.py         # Communication with Breathe Bhutan
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── logger.py           # Logging configuration
├── tests/                  # Unit and integration tests
├── config.py               # Configuration settings
├── requirements.txt        # Project dependencies
└── main.py                 # Application entry point
```

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file:
   ```
   TELEGRAM_API_TOKEN=your_token_here
   EMAIL_SENDER=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   BREATHE_BHUTAN_EMAIL=contact@breathebhutan.com
   ```
4. Run the scraper to collect initial data:
   ```
   python -m scraper.scraper
   ```
5. Start the bot:
   ```
   python main.py
   ```

## Development Guidelines

- **Modular Design**: Each component is independent with clear interfaces
- **Testing**: Unit tests for each module and integration tests for end-to-end flows
- **Logging**: Comprehensive logging for monitoring and debugging
- **Error Handling**: Robust exception handling for API calls and user interactions

## License

This project is proprietary and intended for use by Breathe Bhutan only.

# Breathe Bhutan Telegram Bot - Data Collection

This repository contains structured data for the Breathe Bhutan Telegram bot, a virtual travel agent for planning trips to Bhutan. The data is organized into JSON files by category, providing comprehensive information about Bhutan's tourism offerings.

## Project Overview

The Breathe Bhutan Telegram bot is designed to:
- Help users learn about Bhutan as a travel destination
- Provide information about tours, treks, festivals, and special experiences
- Assist with trip planning and itinerary creation
- Connect interested travelers with Breathe Bhutan's services

This repository focuses on the data collection and organization component of the project, providing structured information that will power the bot's responses.

## Data Structure

The data is organized into the following categories:

| Category | Description | File Path |
|----------|-------------|-----------|
| General | Country information, travel essentials, culture, geography | `data/general/bhutan_info.json` |
| Tours | Cultural tours and specialized tour packages | `data/tours/tours.json` |
| Festivals | Traditional Bhutanese festivals (Tshechus) | `data/festivals/festivals.json` |
| Trekking | Trekking routes and hiking options | `data/trekking/trekking.json` |
| Itineraries | Sample travel itineraries | `data/itineraries/itineraries.json` |
| Special Experiences | Unique activities and experiences | `data/special_experiences/special_experiences.json` |
| Reviews | Customer testimonials | `data/reviews/testimonials.json` |
| Deals | Special offers and promotions | `data/deals/special_offers.json` |

An index of all data files is provided in `data/index.json`.

## Data Format

All data is stored in JSON format with consistent structures within each category. Each data file typically contains:

1. An array of specific entries (e.g., individual tours, festivals)
2. General information about the category
3. Metadata about the information (when applicable)

Example structure for a tour:
```json
{
  "name": "Cultural Tour of Western Bhutan",
  "duration": "7 days",
  "best_season": ["Spring (March-May)", "Autumn (September-November)"],
  "description": "A comprehensive tour of Western Bhutan's cultural highlights...",
  "difficulty": "Easy to Moderate",
  "destinations": ["Paro", "Thimphu", "Punakha"],
  "highlights": ["Tiger's Nest Monastery", "Punakha Dzong", "Traditional farmhouse stay"],
  "ideal_for": ["First-time visitors", "Cultural enthusiasts", "Photography lovers"],
  "image_url": "https://breathebhutan.com/wp-content/uploads/2023/10/cultural-tour-western-bhutan.jpg"
}
```

## Usage in Telegram Bot

This data is designed to be consumed by the Breathe Bhutan Telegram bot. The bot will:

1. Access relevant information based on user queries
2. Format and present the data in a user-friendly way
3. Use the structured data to provide recommendations and answers
4. Enable searches across categories
5. Support the generation of custom itineraries

## Data Maintenance

To keep the data current and accurate:

1. Regular reviews should be conducted, especially for time-sensitive information
2. Festival dates should be updated annually based on the Bhutanese lunar calendar
3. Special offers and deals should be updated seasonally
4. New tours, experiences, and itineraries should be added as they become available
5. Customer testimonials should be refreshed periodically

## Next Steps

After the data collection phase, the project will move on to:

1. Telegram bot development using the Python Telegram Bot API
2. Integration of the structured data with the bot's conversation flows
3. Development of recommendation algorithms
4. Testing with sample user interactions
5. Deployment and maintenance

## Requirements

- Python 3.8+
- JSON parsing capability
- For updating data: text editor or IDE with JSON support

## Contact

For questions or contributions to this data collection:
- Email: info@breathebhutan.com
- Website: https://breathebhutan.com 