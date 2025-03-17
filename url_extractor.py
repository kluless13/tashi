import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extraction.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# URLs organized by category
URLS = {
    "general": [
        "https://www.breathebhutan.com/why-travel-bhutan/",
        "https://www.breathebhutan.com/why-breathe-bhutan/",
        "https://www.breathebhutan.com/travel-guide-and-information-for-bhutan/discount-incentives-for-bhutan-travel-visa-for-year-2023-2024-2025-2026-2027/"
    ],
    "tours": [
        "https://www.breathebhutan.com/cultural-tours-to-bhutan/"
    ],
    "festivals": [
        "https://www.breathebhutan.com/festivalsinbhutan/"
    ],
    "trekking": [
        "https://www.breathebhutan.com/trekking-in-bhutan/"
    ],
    "itineraries": [
        "https://www.breathebhutan.com/travel-itineraries/beyond-the-beaten-path-a-journey-to-gasa-and-laya-gasa-festival-10-days-9-nights/",
        "https://www.breathebhutan.com/travel-itineraries/the-best-of-luxury-travel-in-bhutan-8-days-7-nights/",
        "https://www.breathebhutan.com/travel-itineraries/punakha-festival-bhutan-travel-package/",
        "https://www.breathebhutan.com/travel-itineraries/blissful-west-with-paro-festival-bhutan-travel-package/",
        "https://www.breathebhutan.com/travel-itineraries/thimphu-festival-bhutan-travel-package/",
        "https://www.breathebhutan.com/travel-itineraries/royal-highland-festival-bhutan-travel-package/"
    ],
    "special_experiences": [
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/meditation-yoga-class-in-bhutan/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/consult-a-buddhist-astrologer/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/bhutan-helicopter-rides-and-tours/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/get-a-buddhist-tattoo-in-bhutan/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/consult-a-traditional-medicine-doctor/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/fly-fishing-in-bhutan/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/experience-rural-life-in-bhutan/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/weaving-class-on-traditional-textiles/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/meet-interact-with-bhutanese-personalities/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/travel-package-for-dolls-plushies/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/archery/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/hot-stone-bath/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/night-at-a-monastery/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/basic-painting-art-class/",
        "https://www.breathebhutan.com/special-and-unique-travel-adventures-and-experiences-in-bhutan/nightlife-in-bhutan/"
    ],
    "reviews": [
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/yanai-new-zealand-february-2025/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/jenny-jung-yee-france-malaysia-december-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/tanya-manterfield-cape-town-july-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/janna-taninbaum-new-york-november-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/philipp-wife/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/christine-may-philippines-may-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/marek-family-slovakia-february-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/bobby-paul-new-zealand-may-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/philip-caluya-philippines-spring-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/shaila-jivan-south-africa/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/lisa-pinsely-husband-usa-november-2024/",
        "https://www.breathebhutan.com/our-guests-travelers-review-of-breathe-bhutan/sirinart-husband-usa-september-2024/"
    ],
    "deals": [
        "https://www.breathebhutan.com/travel-deals-and-discount-offers-for-bhutan-travel/offer-at-pemako-in-punakha/"
    ]
}

# Headers to avoid being blocked as a bot
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def fetch_page(url):
    """Fetch the page content with error handling and retries"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

def extract_url_data(url, category):
    """Extract data from a URL based on its category"""
    logger.info(f"Processing {url}")
    
    html_content = fetch_page(url)
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract basic information available on most pages
    title = soup.title.text.strip() if soup.title else ""
    main_content = soup.find('div', class_='container')
    
    # Get the page slug to use as an ID
    path = urlparse(url).path
    slug = path.strip('/').split('/')[-1]
    
    # Base data structure
    data = {
        "id": slug,
        "url": url,
        "title": title,
        "category": category,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Extract category-specific data
    if category == "tours":
        data.update(extract_tour_data(soup))
    elif category == "festivals":
        data.update(extract_festival_data(soup))
    elif category == "trekking":
        data.update(extract_trekking_data(soup))
    elif category == "itineraries":
        data.update(extract_itinerary_data(soup))
    elif category == "special_experiences":
        data.update(extract_special_experience_data(soup))
    elif category == "reviews":
        data.update(extract_review_data(soup))
    elif category == "general":
        data.update(extract_general_info_data(soup))
    elif category == "deals":
        data.update(extract_deal_data(soup))
    
    return data

def extract_tour_data(soup):
    """Extract data specific to tour pages"""
    data = {
        "tours": [],
        "description": ""
    }
    
    # Try to find the main content section
    content_div = soup.find('div', class_='home-content')
    if content_div:
        description_p = content_div.find_all('p')
        data["description"] = " ".join([p.text.strip() for p in description_p])
    
    # Find tour packages
    tour_panels = soup.find_all('div', class_='panel')
    for panel in tour_panels:
        tour = {}
        title_elem = panel.find('h2')
        if title_elem and title_elem.find('a'):
            tour["title"] = title_elem.find('a').text.strip()
            tour["url"] = title_elem.find('a').get('href', '')
        
        excerpt = panel.find('p', class_='excerpt')
        if excerpt:
            tour["description"] = excerpt.text.strip()
        
        image_div = panel.find('div', class_='panel-body')
        if image_div and 'background-image' in image_div.get('style', ''):
            style = image_div.get('style', '')
            image_url = style.split('url(')[1].split(')')[0] if 'url(' in style else ''
            tour["image"] = image_url.strip("'\"")
        
        if tour:
            data["tours"].append(tour)
    
    return data

def extract_festival_data(soup):
    """Extract data specific to festival pages"""
    data = {
        "festivals": [],
        "description": ""
    }
    
    # Try to find the main content section
    content_div = soup.find('div', class_='home-content')
    if content_div:
        description_p = content_div.find_all('p')
        data["description"] = " ".join([p.text.strip() for p in description_p])
    
    # Find festival items
    festival_panels = soup.find_all('div', class_='panel')
    for panel in festival_panels:
        festival = {}
        title_elem = panel.find('h2')
        if title_elem and title_elem.find('a'):
            festival["title"] = title_elem.find('a').text.strip()
            festival["url"] = title_elem.find('a').get('href', '')
        
        excerpt = panel.find('p', class_='excerpt')
        if excerpt:
            festival["description"] = excerpt.text.strip()
        
        # Try to extract dates from title or description
        if "title" in festival:
            import re
            date_match = re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+-\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+', festival["title"])
            if date_match:
                festival["dates"] = date_match.group(0)
        
        image_div = panel.find('div', class_='panel-body')
        if image_div and 'background-image' in image_div.get('style', ''):
            style = image_div.get('style', '')
            image_url = style.split('url(')[1].split(')')[0] if 'url(' in style else ''
            festival["image"] = image_url.strip("'\"")
        
        if festival:
            data["festivals"].append(festival)
    
    return data

def extract_trekking_data(soup):
    """Extract data specific to trekking pages"""
    data = {
        "treks": [],
        "description": ""
    }
    
    # Try to find the main content section
    content_div = soup.find('div', class_='home-content')
    if content_div:
        description_p = content_div.find_all('p')
        data["description"] = " ".join([p.text.strip() for p in description_p])
    
    # Find trek packages
    trek_panels = soup.find_all('div', class_='panel')
    for panel in trek_panels:
        trek = {}
        title_elem = panel.find('h2')
        if title_elem and title_elem.find('a'):
            trek["title"] = title_elem.find('a').text.strip()
            trek["url"] = title_elem.find('a').get('href', '')
        
        excerpt = panel.find('p', class_='excerpt')
        if excerpt:
            trek["description"] = excerpt.text.strip()
        
        # Try to extract duration if available
        if "title" in trek:
            import re
            duration_match = re.search(r'(\d+)\s*Days', trek["title"])
            if duration_match:
                trek["duration_days"] = int(duration_match.group(1))
        
        image_div = panel.find('div', class_='panel-body')
        if image_div and 'background-image' in image_div.get('style', ''):
            style = image_div.get('style', '')
            image_url = style.split('url(')[1].split(')')[0] if 'url(' in style else ''
            trek["image"] = image_url.strip("'\"")
        
        if trek:
            data["treks"].append(trek)
    
    return data

def extract_itinerary_data(soup):
    """Extract data specific to itinerary pages"""
    data = {
        "itinerary_name": "",
        "duration": "",
        "description": "",
        "highlights": [],
        "daily_plan": [],
        "inclusions": [],
        "exclusions": []
    }
    
    # Extract the title/name
    title_elem = soup.find('h1', class_='entry-title')
    if title_elem:
        data["itinerary_name"] = title_elem.text.strip()
    
    # Extract duration from title or content
    if data["itinerary_name"]:
        import re
        duration_match = re.search(r'(\d+)\s*Days', data["itinerary_name"])
        if duration_match:
            data["duration"] = f"{duration_match.group(1)} Days"
    
    # Extract main content
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Extract description
        intro_p = content_div.find_all('p', limit=3)
        data["description"] = " ".join([p.text.strip() for p in intro_p])
        
        # Try to extract highlights
        highlights_h2 = None
        for h2 in content_div.find_all('h2'):
            if 'highlight' in h2.text.lower():
                highlights_h2 = h2
                break
                
        if highlights_h2:
            next_elem = highlights_h2.find_next('ul')
            if next_elem:
                for li in next_elem.find_all('li'):
                    data["highlights"].append(li.text.strip())
        
        # Try to extract daily plan
        days_h2 = []
        for h2 in content_div.find_all(['h2', 'h3']):
            if 'day' in h2.text.lower() and any(char.isdigit() for char in h2.text):
                days_h2.append(h2)
        
        for day_h in days_h2:
            day_title = day_h.text.strip()
            day_content = ""
            next_elem = day_h.find_next_sibling()
            while next_elem and next_elem.name not in ['h2', 'h3'] or ('day' not in next_elem.text.lower() and not any(char.isdigit() for char in next_elem.text)):
                if next_elem.name == 'p':
                    day_content += next_elem.text.strip() + " "
                next_elem = next_elem.find_next_sibling()
                if not next_elem:
                    break
            
            if day_title and day_content:
                data["daily_plan"].append({
                    "title": day_title,
                    "description": day_content.strip()
                })
        
        # Try to extract inclusions/exclusions
        inclusions_h2 = None
        exclusions_h2 = None
        
        for h2 in content_div.find_all(['h2', 'h3']):
            if 'includ' in h2.text.lower() or 'inclus' in h2.text.lower():
                inclusions_h2 = h2
            elif 'exclud' in h2.text.lower() or 'exclus' in h2.text.lower():
                exclusions_h2 = h2
        
        if inclusions_h2:
            next_elem = inclusions_h2.find_next('ul')
            if next_elem:
                for li in next_elem.find_all('li'):
                    data["inclusions"].append(li.text.strip())
        
        if exclusions_h2:
            next_elem = exclusions_h2.find_next('ul')
            if next_elem:
                for li in next_elem.find_all('li'):
                    data["exclusions"].append(li.text.strip())
    
    return data

def extract_special_experience_data(soup):
    """Extract data specific to special experience pages"""
    data = {
        "experience_name": "",
        "description": "",
        "price_info": "",
        "duration": "",
        "images": []
    }
    
    # Extract the title/name
    title_elem = soup.find('h1', class_='entry-title')
    if title_elem:
        data["experience_name"] = title_elem.text.strip()
    
    # Extract main content
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Extract all paragraphs for description
        paragraphs = content_div.find_all('p')
        if paragraphs:
            data["description"] = " ".join([p.text.strip() for p in paragraphs])
        
        # Try to extract price information
        for p in paragraphs:
            if any(price_word in p.text.lower() for price_word in ['price', 'cost', 'fee', 'usd', '$', 'nu']):
                data["price_info"] = p.text.strip()
                break
        
        # Try to extract duration information
        for p in paragraphs:
            if any(time_word in p.text.lower() for time_word in ['hour', 'day', 'duration', 'time']):
                if not any(price_word in p.text.lower() for price_word in ['price', 'cost', 'fee']):
                    data["duration"] = p.text.strip()
                    break
        
        # Extract images
        for img in content_div.find_all('img'):
            src = img.get('src', '')
            if src and src not in data["images"]:
                data["images"].append(src)
    
    return data

def extract_review_data(soup):
    """Extract data specific to review pages"""
    data = {
        "reviewer_name": "",
        "reviewer_origin": "",
        "review_date": "",
        "review_text": "",
        "images": []
    }
    
    # Extract the title containing reviewer info
    title_elem = soup.find('h1', class_='entry-title')
    if title_elem:
        full_title = title_elem.text.strip()
        
        # Try to parse reviewer name and origin
        import re
        reviewer_match = re.match(r'(.+?)(?:,\s*([^–\-]+))?(?:\s*[-–]\s*(.+))?$', full_title)
        if reviewer_match:
            data["reviewer_name"] = reviewer_match.group(1).strip()
            if reviewer_match.group(2):
                data["reviewer_origin"] = reviewer_match.group(2).strip()
            if reviewer_match.group(3):
                data["review_date"] = reviewer_match.group(3).strip()
    
    # Extract review content
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        paragraphs = content_div.find_all('p')
        if paragraphs:
            data["review_text"] = " ".join([p.text.strip() for p in paragraphs])
        
        # Extract images
        for img in content_div.find_all('img'):
            src = img.get('src', '')
            if src and src not in data["images"]:
                data["images"].append(src)
    
    return data

def extract_general_info_data(soup):
    """Extract general information from pages"""
    data = {
        "content": "",
        "sections": []
    }
    
    # Extract main content
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Get all paragraphs for main content
        all_paragraphs = content_div.find_all('p')
        if all_paragraphs:
            data["content"] = " ".join([p.text.strip() for p in all_paragraphs])
        
        # Try to identify sections by headings
        for heading in content_div.find_all(['h2', 'h3']):
            section = {
                "title": heading.text.strip(),
                "content": ""
            }
            
            # Get content following this heading until the next heading
            next_elem = heading.find_next_sibling()
            while next_elem and next_elem.name not in ['h2', 'h3']:
                if next_elem.name == 'p':
                    section["content"] += next_elem.text.strip() + " "
                elif next_elem.name == 'ul':
                    for li in next_elem.find_all('li'):
                        section["content"] += "• " + li.text.strip() + " "
                
                next_elem = next_elem.find_next_sibling()
                if not next_elem:
                    break
            
            if section["content"]:
                section["content"] = section["content"].strip()
                data["sections"].append(section)
    
    return data

def extract_deal_data(soup):
    """Extract data specific to deals and offers pages"""
    data = {
        "deal_title": "",
        "description": "",
        "valid_dates": "",
        "price_info": "",
        "images": []
    }
    
    # Extract the title
    title_elem = soup.find('h1', class_='entry-title')
    if title_elem:
        data["deal_title"] = title_elem.text.strip()
    
    # Extract main content
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Extract all paragraphs for description
        paragraphs = content_div.find_all('p')
        if paragraphs:
            data["description"] = " ".join([p.text.strip() for p in paragraphs])
        
        # Try to extract dates and price information
        for p in paragraphs:
            if any(date_word in p.text.lower() for date_word in ['valid', 'date', 'period', 'until', 'from']):
                data["valid_dates"] = p.text.strip()
            
            if any(price_word in p.text.lower() for price_word in ['price', 'cost', 'fee', 'discount', 'offer', 'save', 'usd', '$', 'nu']):
                data["price_info"] = p.text.strip()
        
        # Extract images
        for img in content_div.find_all('img'):
            src = img.get('src', '')
            if src and src not in data["images"]:
                data["images"].append(src)
    
    return data

def save_to_json(data, category, slug):
    """Save extracted data to a JSON file"""
    if not data:
        logger.error(f"No data to save for {slug}")
        return
    
    directory = f"data/{category}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/{slug}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved data to {filename}")

def create_category_index(category, items):
    """Create an index file for a category containing all items"""
    directory = f"data/{category}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/index.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created index for {category} with {len(items)} items")

def main():
    """Main function to process all URLs"""
    logger.info("Starting extraction process")
    
    # Process each category
    for category, urls in URLS.items():
        logger.info(f"Processing category: {category}")
        category_items = []
        
        for url in urls:
            # Get the slug from the URL
            path = urlparse(url).path
            slug = path.strip('/').split('/')[-1]
            
            # Extract data
            data = extract_url_data(url, category)
            if data:
                # Save individual file
                save_to_json(data, category, slug)
                
                # Add to category index
                summary = {
                    "id": slug,
                    "url": url,
                    "title": data.get("title", ""),
                    "category": category
                }
                
                # Add more specific fields based on category
                if category == "tours" and "tours" in data:
                    summary["tours_count"] = len(data["tours"])
                elif category == "festivals" and "festivals" in data:
                    summary["festivals_count"] = len(data["festivals"])
                elif category == "trekking" and "treks" in data:
                    summary["treks_count"] = len(data["treks"])
                elif category == "itineraries":
                    summary["itinerary_name"] = data.get("itinerary_name", "")
                    summary["duration"] = data.get("duration", "")
                elif category == "special_experiences":
                    summary["experience_name"] = data.get("experience_name", "")
                    summary["price_info"] = data.get("price_info", "")
                elif category == "reviews":
                    summary["reviewer_name"] = data.get("reviewer_name", "")
                    summary["reviewer_origin"] = data.get("reviewer_origin", "")
                    summary["review_date"] = data.get("review_date", "")
                
                category_items.append(summary)
            
            # Sleep to avoid overloading the server
            time.sleep(1)
        
        # Create category index file
        create_category_index(category, category_items)
    
    logger.info("Extraction process completed")

if __name__ == "__main__":
    main() 