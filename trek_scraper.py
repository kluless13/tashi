#!/usr/bin/env python3
import json
import os
import requests
from bs4 import BeautifulSoup
import time
import logging
import re
import datetime
import asyncio
from dotenv import load_dotenv
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import ExtractionStrategy, NoExtractionStrategy
from typing import List, Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("trek_scraping.log"), logging.StreamHandler()]
)
logger = logging.getLogger("trek_scraper")

# Create data directory if it doesn't exist
os.makedirs("data/trekking", exist_ok=True)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_soup(url, retries=3, delay=2):
    """Get BeautifulSoup object from URL with retry logic."""
    for attempt in range(retries):
        try:
            logger.info(f"Fetching {url}")
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt+1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    logger.error(f"Failed to fetch {url} after {retries} attempts")
    return None

def setup_crawler() -> WebCrawler:
    """Set up the crawl4ai crawler"""
    try:
        # Try to set up crawler with default settings first
        try:
            crawler = WebCrawler(verbose=True)
            crawler.warmup()
            logger.info("Successfully set up crawl4ai crawler")
            return crawler
        except Exception as e:
            if "lxml.parser" in str(e):
                logger.warning("lxml parser issue detected. Attempting alternate setup...")
                # Try an alternative setup that doesn't rely on lxml
                crawler = WebCrawler(verbose=True)
                # Skip warmup if it's causing lxml-related issues
                logger.info("Set up crawl4ai crawler with alternative configuration")
                return crawler
            else:
                raise  # Re-raise if it's not the lxml issue
    except Exception as e:
        logger.error(f"Error setting up crawl4ai crawler: {e}")
        raise

def crawl_trek_page(crawler: WebCrawler, url: str) -> Optional[Dict]:
    """Crawl a trek page using crawl4ai"""
    try:
        logger.info(f"Crawling {url} with crawl4ai")
        # Use NoExtractionStrategy to avoid lxml parser issues
        extraction_strategy = NoExtractionStrategy()
        result = crawler.run(
            url, 
            word_count_threshold=50, 
            bypass_cache=False,
            extraction_strategy=extraction_strategy
        )
        return result
    except Exception as e:
        error_msg = str(e)
        if "lxml.parser" in error_msg:
            logger.warning(f"lxml parser issue when crawling {url}. Defaulting to manual extraction.")
        else:
            logger.error(f"Error crawling {url} with crawl4ai: {e}")
        return None

def extract_trek_urls_from_sitemap():
    """Extract trek URLs from the sitemap data."""
    try:
        with open('data/sitemap.txt', 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
            
        # Extract all URLs from sitemap
        urls = re.findall(r'<loc>(https://www\.breathebhutan\.com/.*?)</loc>', sitemap_content)
        
        # Filter to include only trek-related URLs
        trek_urls = []
        for url in urls:
            if 'trekking-in-bhutan/' in url and not url.endswith('trekking-in-bhutan/') and 'category' not in url:
                trek_urls.append(url)
                
        logger.info(f"Found {len(trek_urls)} trek URLs from sitemap")
        
        # If no trek URLs found in sitemap, try to get them directly from the main page
        if not trek_urls:
            trek_urls = extract_trek_urls_from_main_page()
        
        return trek_urls
    except Exception as e:
        logger.error(f"Error extracting trek URLs from sitemap: {e}")
        # Fallback to direct extraction
        logger.info("Falling back to direct extraction from main page")
        return extract_trek_urls_from_main_page()

def extract_trek_urls_from_main_page():
    """Extract trek URLs directly from the main trekking page."""
    try:
        main_url = "https://www.breathebhutan.com/trekking-in-bhutan/"
        soup = get_soup(main_url)
        trek_urls = []
        
        if soup:
            # Find all "Explore" buttons for treks
            trek_links = soup.select('a.btn.btn-travel')
            for link in trek_links:
                if "Explore" in link.text and link.get('href'):
                    trek_url = link.get('href')
                    trek_urls.append(trek_url)
                    logger.info(f"Found trek URL from main page: {trek_url}")
        
        return trek_urls
    except Exception as e:
        logger.error(f"Error extracting trek URLs from main page: {e}")
        return []

def extract_content_from_url(url):
    """Extract the main content from a URL."""
    try:
        soup = get_soup(url)
        if not soup:
            return ""
        
        # Extract the title
        title = ""
        title_element = soup.select_one('h1.entry-title')
        if title_element:
            title = title_element.text.strip()
        
        # Extract the main content
        content = ""
        content_element = soup.select_one('.entry-content')
        if content_element:
            content = content_element.get_text(separator="\n\n")
            
        # Combine title and content
        full_content = f"TITLE: {title}\n\nCONTENT:\n{content}"
        return full_content
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""

def call_groq_api(content, url):
    """Call the Groq API to extract structured trek information."""
    try:
        if not GROQ_API_KEY:
            logger.error("Groq API key not configured. Please set GROQ_API_KEY in .env file.")
            return None
            
        logger.info(f"Calling Groq API for {url}")
        
        # Prepare the prompt for extracting structured trek information
        prompt = f"""
        You are an expert in extracting structured information from trekking websites. 
        Your task is to carefully analyze the following content from a trek webpage and extract structured information about the trek.
        
        Extract the following information in a structured JSON format:
        1. name: The official name of the trek
        2. id: A normalized ID for the trek (lowercase, hyphens instead of spaces)
        3. description: A concise description of the trek (1-3 paragraphs max)
        4. duration: The duration in days and nights as a nested object with "days" and "nights" fields
        5. difficulty_level: The difficulty level (Easy, Moderate, Hard, etc.)
        6. max_altitude: The maximum altitude reached during the trek (in meters)
        7. min_altitude: The minimum altitude during the trek (in meters)
        8. best_season: When is the best time to do this trek
        9. start_point: Where the trek starts
        10. end_point: Where the trek ends
        11. highlights: A list of key highlights or attractions of the trek
        12. itinerary: A detailed day-by-day itinerary with each item containing:
            - day: The day number
            - title: The title or name of this day's section
            - description: A detailed description of the day's activities
            - distance: The distance covered (if available)
            - duration: The walking/trekking time (if available)
            - accommodation: Where trekkers stay (if available)
            - meals: Meals included (if available)
            - altitude: Any altitude information for this day (if available)

        Here's the webpage content:
        URL: {url}
        ---
        {content}
        ---
        
        Return ONLY the JSON object with no additional commentary. Parse the itinerary carefully from the content.
        The JSON should be valid and properly structured, with nested objects where appropriate.
        If certain information is not available, use null or an empty array [] for that field rather than omitting it.
        """
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mixtral-8x7b-32768",  # Using Mixtral model for better extraction
            "messages": [
                {"role": "system", "content": "You are an expert at extracting structured information from text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1  # Lower temperature for more deterministic responses
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Extract the JSON response
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Try to parse the content as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # If direct parsing fails, try to extract JSON part from the content
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from Groq API response for {url}")
                        return None
                else:
                    logger.error(f"No JSON found in Groq API response for {url}")
                    return None
        else:
            logger.error(f"Unexpected Groq API response format for {url}")
            return None
    except Exception as e:
        logger.error(f"Error calling Groq API for {url}: {e}")
        return None

def extract_trek_details_from_crawl4ai(page_data) -> Dict[str, Any]:
    """Extract trek details from crawl4ai page data"""
    try:
        url = page_data.url if hasattr(page_data, 'url') else ''
        logger.info(f"Extracting trek details from crawl4ai result for {url}")
        
        # Extract the URL ID
        trek_id = ""
        trek_name = "Unknown Trek"
        if 'trekking-in-bhutan/' in url:
            trek_id = url.split('trekking-in-bhutan/')[1].rstrip('/')
            # Generate a human-readable trek name from the URL
            trek_name = trek_id.replace('-', ' ').title()
        
        # Extract title - if present in crawl4ai results, otherwise use URL-derived name
        title = ""
        if hasattr(page_data, 'title') and page_data.title:
            title = page_data.title
        else:
            # If no title in crawl4ai result, use the URL-based name
            title = trek_name
        
        # Extract description - this is more challenging with NoExtractionStrategy
        description = ""
        
        # Use raw_html if available
        if hasattr(page_data, 'raw_html') and page_data.raw_html:
            # Parse HTML with BeautifulSoup using html.parser instead of lxml
            try:
                soup = BeautifulSoup(page_data.raw_html, 'html.parser')
                
                # Extract description from main content
                main_content = soup.select_one('.entry-content')
                if main_content and main_content.p:
                    description = main_content.p.text.strip()
            except Exception as e:
                logger.error(f"Error parsing HTML from crawl4ai: {e}")
        
        # Extract image URL
        image_url = ""
        if hasattr(page_data, 'images') and page_data.images:
            for img in page_data.images:
                if hasattr(img, 'src') and img.src:
                    image_url = img.src
                    break
        
        # Construct basic data
        trek_data = {
            "id": trek_id,
            "name": title,
            "description": description,
            "url": url,
            "image_url": image_url
        }
        
        # We'll enhance this with Groq API data later
        return trek_data
    except Exception as e:
        logger.error(f"Error extracting details from crawl4ai result: {e}")
        # Even if extraction fails, try to get basic info from URL
        url = page_data.url if hasattr(page_data, 'url') else ""
        trek_id = ""
        trek_name = "Unknown Trek"
        if 'trekking-in-bhutan/' in url:
            trek_id = url.split('trekking-in-bhutan/')[1].rstrip('/')
            trek_name = trek_id.replace('-', ' ').title()
        return {"url": url, "id": trek_id, "name": trek_name}

def merge_trek_data(crawl4ai_data, groq_data):
    """Merge trek data from crawl4ai and Groq API"""
    if not groq_data:
        return crawl4ai_data
        
    # Start with the crawl4ai data
    merged_data = crawl4ai_data.copy()
    
    # Update with Groq data, which typically has more detailed extraction
    for key, value in groq_data.items():
        if key not in merged_data or not merged_data[key]:
            merged_data[key] = value
        elif key == "itinerary" and value:
            # For itinerary, prefer Groq's structuring if available
            merged_data[key] = value
            
    return merged_data

def extract_general_trekking_info():
    """Extract general information about trekking in Bhutan."""
    try:
        main_url = "https://www.breathebhutan.com/trekking-in-bhutan/"
        guide_url = "https://www.breathebhutan.com/travel-guide-and-information-for-bhutan/a-brief-guide-on-trekking-in-bhutan/"
        packing_url = "https://www.breathebhutan.com/travel-guide-and-information-for-bhutan/packing-list-for-trekking-in-bhutan/"
        
        general_info = {
            "description": "",
            "trekking_seasons": "",
            "trekking_permits": "",
            "essentials_to_pack": [],
            "health_considerations": []
        }
        
        # Get main page info
        soup = get_soup(main_url)
        if soup:
            content = soup.select_one('.entry-content')
            if content and content.p:
                general_info["description"] = content.p.text.strip()
                logger.info(f"Extracted general trekking description: {general_info['description'][:100]}...")
        
        # Get guide info using Groq API
        content = extract_content_from_url(guide_url)
        if content:
            prompt = f"""
            Extract the following information from this guide about trekking in Bhutan:
            1. best_seasons: A detailed description of the best seasons for trekking in Bhutan
            2. permits: Information about permits required for trekking
            
            The content is:
            {content}
            
            Return ONLY a JSON object with these two keys and their values.
            """
            
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": "You are an expert at extracting information."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
                
                response = requests.post(GROQ_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    try:
                        guide_info = json.loads(content)
                        if "best_seasons" in guide_info:
                            general_info["trekking_seasons"] = guide_info["best_seasons"]
                        if "permits" in guide_info:
                            general_info["trekking_permits"] = guide_info["permits"]
                    except:
                        pass
            except Exception as e:
                logger.error(f"Error getting guide info from Groq: {e}")
        
        # Get packing list
        soup = get_soup(packing_url)
        if soup:
            content = soup.select_one('.entry-content')
            if content:
                # Look for lists
                for ul in content.find_all('ul'):
                    items = [li.text.strip() for li in ul.find_all('li')]
                    if items:
                        if not general_info["essentials_to_pack"]:
                            general_info["essentials_to_pack"] = items
                            logger.info(f"Extracted {len(items)} essentials to pack")
                        elif not general_info["health_considerations"]:
                            general_info["health_considerations"] = items
                            logger.info(f"Extracted {len(items)} health considerations")
        
        return general_info
    except Exception as e:
        logger.error(f"Error extracting general trekking info: {e}")
        return {"description": "", "trekking_seasons": "", "trekking_permits": "", "essentials_to_pack": [], "health_considerations": []}

def process_trek_url(url: str, crawler: WebCrawler) -> Dict[str, Any]:
    """Process a single trek URL using both crawl4ai and Groq API"""
    try:
        logger.info(f"Processing trek at {url}")
        
        # First create a basic trek object from the URL (as fallback)
        trek_id = ""
        trek_name = "Unknown Trek"
        if 'trekking-in-bhutan/' in url:
            trek_id = url.split('trekking-in-bhutan/')[1].rstrip('/')
            trek_name = trek_id.replace('-', ' ').title()
        
        basic_trek_data = {
            "id": trek_id,
            "name": trek_name,
            "url": url
        }
        
        # Step 1: Crawl the page with crawl4ai
        page_data = crawl_trek_page(crawler, url)
        
        # Step 2: Extract basic information from crawl4ai result
        if page_data:
            try:
                trek_data_from_crawler = extract_trek_details_from_crawl4ai(page_data)
            except Exception as e:
                logger.error(f"Error processing crawl4ai data: {e}")
                trek_data_from_crawler = basic_trek_data
        else:
            trek_data_from_crawler = basic_trek_data
        
        # Step 3: Extract content for Groq processing
        content = extract_content_from_url(url)
        
        # Step 4: Call Groq API to extract detailed structured information
        if content:
            try:
                trek_data_from_groq = call_groq_api(content, url)
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                trek_data_from_groq = None
        else:
            trek_data_from_groq = None
            
        # Step 5: Merge data from both sources
        merged_data = merge_trek_data(trek_data_from_crawler, trek_data_from_groq)
        
        return merged_data
    except Exception as e:
        logger.error(f"Error processing trek URL {url}: {e}")
        # Provide basic information even if processing fails
        trek_id = ""
        trek_name = "Unknown Trek"
        if 'trekking-in-bhutan/' in url:
            trek_id = url.split('trekking-in-bhutan/')[1].rstrip('/')
            trek_name = trek_id.replace('-', ' ').title()
        return {"url": url, "error": str(e), "id": trek_id, "name": trek_name}

def main():
    try:
        # Step 1: Get trek URLs from sitemap or main page
        trek_urls = extract_trek_urls_from_sitemap()
        
        if not trek_urls:
            logger.error("No trek URLs found. Exiting.")
            return
            
        # Step 2: Set up crawl4ai crawler
        crawler = setup_crawler()
        
        # Step 3: Process each trek URL with combination of crawl4ai and Groq
        treks_data = []
        for url in trek_urls:
            # Process URLs sequentially to be gentle with the server
            trek_data = process_trek_url(url, crawler)
            if trek_data and "name" in trek_data:
                treks_data.append(trek_data)
                logger.info(f"Successfully extracted data for {trek_data['name']}")
            else:
                logger.warning(f"Failed to extract complete data for {url}")
            
            time.sleep(1)  # Be polite with requests
        
        # Step 4: Extract general trekking information
        general_info = extract_general_trekking_info()
        
        # Step 5: Save the data
        output_data = {
            "treks": treks_data,
            "general_info": general_info,
            "metadata": {
                "count": len(treks_data),
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "https://www.breathebhutan.com/trekking-in-bhutan/",
                "extraction_methods": ["crawl4ai", "Groq API (mixtral-8x7b-32768)"]
            }
        }
        
        # Print summary before saving
        logger.info(f"Extracted data for {len(treks_data)} treks:")
        for trek in treks_data:
            logger.info(f"  - {trek.get('name', 'Unknown')} (Itinerary days: {len(trek.get('itinerary', []))})")
        
        with open("data/trekking/trekking.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully saved data for {len(treks_data)} treks to data/trekking/trekking.json")
    
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")

if __name__ == "__main__":
    main() 