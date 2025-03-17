import asyncio
import json
import logging
import os
import re
import time
from urllib.parse import urlparse
from playwright.async_api import async_playwright

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

async def extract_url_data(page, url, category):
    """Extract data from a URL based on its category"""
    logger.info(f"Processing {url}")
    
    # Get the page slug to use as an ID
    path = urlparse(url).path
    slug = path.strip('/').split('/')[-1]
    
    try:
        # Navigate to the page with a timeout of 60 seconds
        await page.goto(url, timeout=60000)
        # Wait for the content to be loaded
        await page.wait_for_load_state('networkidle')
        
        # Extract title
        title = await page.title()
        
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
            data.update(await extract_tour_data(page))
        elif category == "festivals":
            data.update(await extract_festival_data(page))
        elif category == "trekking":
            data.update(await extract_trekking_data(page))
        elif category == "itineraries":
            data.update(await extract_itinerary_data(page))
        elif category == "special_experiences":
            data.update(await extract_special_experience_data(page))
        elif category == "reviews":
            data.update(await extract_review_data(page))
        elif category == "general":
            data.update(await extract_general_info_data(page))
        elif category == "deals":
            data.update(await extract_deal_data(page))
        
        return data
    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return {
            "id": slug,
            "url": url,
            "title": title if 'title' in locals() else "",
            "category": category,
            "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

async def extract_tour_data(page):
    """Extract data specific to tour pages"""
    data = {
        "tours": [],
        "description": ""
    }
    
    # Extract description
    description_selector = '.entry-content p, .home-content p'
    description_elements = await page.query_selector_all(description_selector)
    description_texts = []
    for elem in description_elements:
        text = await elem.text_content()
        if text.strip():
            description_texts.append(text.strip())
    
    data["description"] = " ".join(description_texts)
    
    # Extract tours
    tour_panels = await page.query_selector_all('.panel')
    for panel in tour_panels:
        tour = {}
        
        # Extract title and URL
        title_elem = await panel.query_selector('h2 a')
        if title_elem:
            tour["title"] = await title_elem.text_content()
            tour["url"] = await title_elem.get_attribute('href')
        
        # Extract description
        excerpt = await panel.query_selector('.excerpt')
        if excerpt:
            tour["description"] = await excerpt.text_content()
        
        # Extract image
        image_div = await panel.query_selector('.panel-body')
        if image_div:
            style = await image_div.get_attribute('style')
            if style and 'background-image' in style:
                match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                if match:
                    tour["image"] = match.group(1)
        
        if tour.get("title"):
            data["tours"].append(tour)
    
    return data

async def extract_festival_data(page):
    """Extract data specific to festival pages"""
    data = {
        "festivals": [],
        "description": ""
    }
    
    # Extract description
    description_selector = '.entry-content p, .home-content p'
    description_elements = await page.query_selector_all(description_selector)
    description_texts = []
    for elem in description_elements:
        text = await elem.text_content()
        if text.strip():
            description_texts.append(text.strip())
    
    data["description"] = " ".join(description_texts)
    
    # Extract festivals
    festival_panels = await page.query_selector_all('.panel')
    
    # If no panels found, try to extract from article elements
    if not festival_panels:
        festival_articles = await page.query_selector_all('article')
        for article in festival_articles:
            festival = {}
            
            # Extract title
            title_elem = await article.query_selector('h2.entry-title a, h1.entry-title')
            if title_elem:
                festival["title"] = await title_elem.text_content()
                
                # Try to get URL if it's a link
                href = await title_elem.get_attribute('href')
                if href:
                    festival["url"] = href
            
            # Extract content
            content_elem = await article.query_selector('.entry-content')
            if content_elem:
                festival["description"] = await content_elem.text_content()
            
            # Extract dates from title or content
            if festival.get("title"):
                date_match = re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+-\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+', festival["title"])
                if date_match:
                    festival["dates"] = date_match.group(0)
            
            # Extract image
            img_elem = await article.query_selector('img')
            if img_elem:
                festival["image"] = await img_elem.get_attribute('src')
            
            if festival.get("title"):
                data["festivals"].append(festival)
    else:
        # Process panels if found
        for panel in festival_panels:
            festival = {}
            
            # Extract title and URL
            title_elem = await panel.query_selector('h2 a')
            if title_elem:
                festival["title"] = await title_elem.text_content()
                festival["url"] = await title_elem.get_attribute('href')
            
            # Extract description
            excerpt = await panel.query_selector('.excerpt')
            if excerpt:
                festival["description"] = await excerpt.text_content()
            
            # Extract dates from title
            if festival.get("title"):
                date_match = re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+-\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+', festival["title"])
                if date_match:
                    festival["dates"] = date_match.group(0)
            
            # Extract image
            image_div = await panel.query_selector('.panel-body')
            if image_div:
                style = await image_div.get_attribute('style')
                if style and 'background-image' in style:
                    match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                    if match:
                        festival["image"] = match.group(1)
            
            if festival.get("title"):
                data["festivals"].append(festival)
    
    # If still no festivals found, try to get content from a list
    if not data["festivals"]:
        festivals_list = await page.query_selector_all('ul li')
        for item in festivals_list:
            item_text = await item.text_content()
            # Look for festival-like content (containing dates/months)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            if any(month in item_text for month in months) or re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+', item_text):
                festival = {
                    "title": item_text,
                    "description": item_text
                }
                
                # Try to extract dates
                date_match = re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+-\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+', item_text)
                if date_match:
                    festival["dates"] = date_match.group(0)
                
                data["festivals"].append(festival)
    
    return data

async def extract_trekking_data(page):
    """Extract data specific to trekking pages"""
    data = {
        "treks": [],
        "description": ""
    }
    
    # Extract description
    description_selector = '.entry-content p, .home-content p'
    description_elements = await page.query_selector_all(description_selector)
    description_texts = []
    for elem in description_elements:
        text = await elem.text_content()
        if text.strip():
            description_texts.append(text.strip())
    
    data["description"] = " ".join(description_texts)
    
    # Extract treks
    trek_panels = await page.query_selector_all('.panel')
    for panel in trek_panels:
        trek = {}
        
        # Extract title and URL
        title_elem = await panel.query_selector('h2 a')
        if title_elem:
            trek["title"] = await title_elem.text_content()
            trek["url"] = await title_elem.get_attribute('href')
        
        # Extract description
        excerpt = await panel.query_selector('.excerpt')
        if excerpt:
            trek["description"] = await excerpt.text_content()
        
        # Extract duration from title
        if trek.get("title"):
            duration_match = re.search(r'(\d+)\s*Days', trek["title"])
            if duration_match:
                trek["duration_days"] = int(duration_match.group(1))
        
        # Extract image
        image_div = await panel.query_selector('.panel-body')
        if image_div:
            style = await image_div.get_attribute('style')
            if style and 'background-image' in style:
                match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                if match:
                    trek["image"] = match.group(1)
        
        if trek.get("title"):
            data["treks"].append(trek)
    
    return data

async def extract_itinerary_data(page):
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
    
    # Extract title
    title_elem = await page.query_selector('h1.entry-title')
    if title_elem:
        data["itinerary_name"] = await title_elem.text_content()
    
    # Extract duration from title
    if data["itinerary_name"]:
        duration_match = re.search(r'(\d+)\s*Days', data["itinerary_name"])
        if duration_match:
            data["duration"] = f"{duration_match.group(1)} Days"
    
    # Extract description
    content_div = await page.query_selector('.entry-content')
    if content_div:
        # Get first few paragraphs for description
        desc_paragraphs = await content_div.query_selector_all('p')
        desc_texts = []
        for i, p in enumerate(desc_paragraphs):
            if i < 3:  # First 3 paragraphs
                text = await p.text_content()
                if text.strip():
                    desc_texts.append(text.strip())
        data["description"] = " ".join(desc_texts)
        
        # Extract highlights
        highlights_h2 = None
        h2_elements = await content_div.query_selector_all('h2')
        for h2 in h2_elements:
            h2_text = await h2.text_content()
            if 'highlight' in h2_text.lower():
                highlights_h2 = h2
                break
        
        if highlights_h2:
            # Find the next ul element
            ul_after_highlights = None
            sibling = highlights_h2
            while True:
                sibling = await page.evaluate("el => el.nextElementSibling", sibling)
                if not sibling:
                    break
                if await page.evaluate("el => el.tagName.toLowerCase()", sibling) == 'ul':
                    ul_after_highlights = sibling
                    break
            
            if ul_after_highlights:
                list_items = await page.evaluate("ul => Array.from(ul.querySelectorAll('li')).map(li => li.textContent)", ul_after_highlights)
                data["highlights"] = list_items
        
        # Extract daily plan
        day_headings = []
        headings = await content_div.query_selector_all('h2, h3')
        for heading in headings:
            heading_text = await heading.text_content()
            if 'day' in heading_text.lower() and re.search(r'\d+', heading_text):
                day_headings.append(heading)
        
        for day_heading in day_headings:
            day_title = await day_heading.text_content()
            day_content = ""
            
            # Get content until next heading
            next_elem = day_heading
            while True:
                next_elem = await page.evaluate("el => el.nextElementSibling", next_elem)
                if not next_elem:
                    break
                
                elem_tag = await page.evaluate("el => el.tagName.toLowerCase()", next_elem)
                if elem_tag in ['h2', 'h3']:
                    next_heading_text = await page.evaluate("el => el.textContent", next_elem)
                    if 'day' in next_heading_text.lower() and re.search(r'\d+', next_heading_text):
                        break
                
                if elem_tag == 'p':
                    paragraph_text = await page.evaluate("el => el.textContent", next_elem)
                    day_content += paragraph_text.strip() + " "
            
            if day_title and day_content:
                data["daily_plan"].append({
                    "title": day_title.strip(),
                    "description": day_content.strip()
                })
        
        # Extract inclusions/exclusions
        for heading in headings:
            heading_text = await heading.text_content()
            heading_text_lower = heading_text.lower()
            
            if 'includ' in heading_text_lower or 'inclus' in heading_text_lower:
                # Find the next ul element
                ul_after_heading = None
                sibling = heading
                while True:
                    sibling = await page.evaluate("el => el.nextElementSibling", sibling)
                    if not sibling:
                        break
                    if await page.evaluate("el => el.tagName.toLowerCase()", sibling) == 'ul':
                        ul_after_heading = sibling
                        break
                
                if ul_after_heading:
                    list_items = await page.evaluate("ul => Array.from(ul.querySelectorAll('li')).map(li => li.textContent)", ul_after_heading)
                    data["inclusions"] = list_items
            
            elif 'exclud' in heading_text_lower or 'exclus' in heading_text_lower:
                # Find the next ul element
                ul_after_heading = None
                sibling = heading
                while True:
                    sibling = await page.evaluate("el => el.nextElementSibling", sibling)
                    if not sibling:
                        break
                    if await page.evaluate("el => el.tagName.toLowerCase()", sibling) == 'ul':
                        ul_after_heading = sibling
                        break
                
                if ul_after_heading:
                    list_items = await page.evaluate("ul => Array.from(ul.querySelectorAll('li')).map(li => li.textContent)", ul_after_heading)
                    data["exclusions"] = list_items
    
    return data

async def extract_special_experience_data(page):
    """Extract data specific to special experience pages"""
    data = {
        "experience_name": "",
        "description": "",
        "price_info": "",
        "duration": "",
        "images": []
    }
    
    # Extract title
    title_elem = await page.query_selector('h1.entry-title')
    if title_elem:
        data["experience_name"] = await title_elem.text_content()
    
    # Extract content
    content_div = await page.query_selector('.entry-content')
    if content_div:
        # Extract all paragraphs for description
        paragraphs = await content_div.query_selector_all('p')
        paragraph_texts = []
        for p in paragraphs:
            paragraph_texts.append(await p.text_content())
        
        data["description"] = " ".join(paragraph_texts)
        
        # Try to find price information
        for text in paragraph_texts:
            text_lower = text.lower()
            if any(price_word in text_lower for price_word in ['price', 'cost', 'fee', 'usd', '$', 'nu']):
                data["price_info"] = text
                break
        
        # Try to find duration information
        for text in paragraph_texts:
            text_lower = text.lower()
            if any(time_word in text_lower for time_word in ['hour', 'day', 'duration', 'time']):
                if not any(price_word in text_lower for price_word in ['price', 'cost', 'fee']):
                    data["duration"] = text
                    break
        
        # Extract images
        images = await content_div.query_selector_all('img')
        for img in images:
            src = await img.get_attribute('src')
            if src and src not in data["images"]:
                data["images"].append(src)
    
    return data

async def extract_review_data(page):
    """Extract data specific to review pages"""
    data = {
        "reviewer_name": "",
        "reviewer_origin": "",
        "review_date": "",
        "review_text": "",
        "images": []
    }
    
    # Extract title
    title_elem = await page.query_selector('h1.entry-title')
    if title_elem:
        full_title = await title_elem.text_content()
        
        # Try to parse reviewer name and origin
        reviewer_match = re.match(r'(.+?)(?:,\s*([^–\-]+))?(?:\s*[-–]\s*(.+))?$', full_title)
        if reviewer_match:
            data["reviewer_name"] = reviewer_match.group(1).strip() if reviewer_match.group(1) else ""
            data["reviewer_origin"] = reviewer_match.group(2).strip() if reviewer_match.group(2) else ""
            data["review_date"] = reviewer_match.group(3).strip() if reviewer_match.group(3) else ""
    
    # Extract content
    content_div = await page.query_selector('.entry-content')
    if content_div:
        # Extract all paragraphs for review text
        paragraphs = await content_div.query_selector_all('p')
        paragraph_texts = []
        for p in paragraphs:
            paragraph_texts.append(await p.text_content())
        
        data["review_text"] = " ".join(paragraph_texts)
        
        # Extract images
        images = await content_div.query_selector_all('img')
        for img in images:
            src = await img.get_attribute('src')
            if src and src not in data["images"]:
                data["images"].append(src)
    
    return data

async def extract_general_info_data(page):
    """Extract general information from pages"""
    data = {
        "content": "",
        "sections": []
    }
    
    # Extract main content
    content_div = await page.query_selector('.entry-content')
    if content_div:
        # Get all paragraphs for main content
        paragraphs = await content_div.query_selector_all('p')
        paragraph_texts = []
        for p in paragraphs:
            paragraph_texts.append(await p.text_content())
        
        data["content"] = " ".join(paragraph_texts)
        
        # Try to identify sections by headings
        headings = await content_div.query_selector_all('h2, h3')
        for heading in headings:
            heading_text = await heading.text_content()
            section = {
                "title": heading_text.strip(),
                "content": ""
            }
            
            # Get content until next heading
            next_elem = heading
            while True:
                next_elem = await page.evaluate("el => el.nextElementSibling", next_elem)
                if not next_elem:
                    break
                
                elem_tag = await page.evaluate("el => el.tagName.toLowerCase()", next_elem)
                if elem_tag in ['h2', 'h3']:
                    break
                
                if elem_tag == 'p':
                    paragraph_text = await page.evaluate("el => el.textContent", next_elem)
                    section["content"] += paragraph_text.strip() + " "
                elif elem_tag == 'ul':
                    list_items = await page.evaluate("ul => Array.from(ul.querySelectorAll('li')).map(li => li.textContent)", next_elem)
                    for item in list_items:
                        section["content"] += "• " + item.strip() + " "
            
            if section["content"]:
                section["content"] = section["content"].strip()
                data["sections"].append(section)
    
    return data

async def extract_deal_data(page):
    """Extract data specific to deals and offers pages"""
    data = {
        "deal_title": "",
        "description": "",
        "valid_dates": "",
        "price_info": "",
        "images": []
    }
    
    # Extract title
    title_elem = await page.query_selector('h1.entry-title')
    if title_elem:
        data["deal_title"] = await title_elem.text_content()
    
    # Extract content
    content_div = await page.query_selector('.entry-content')
    if content_div:
        # Extract all paragraphs for description
        paragraphs = await content_div.query_selector_all('p')
        paragraph_texts = []
        for p in paragraphs:
            paragraph_texts.append(await p.text_content())
        
        data["description"] = " ".join(paragraph_texts)
        
        # Try to find date and price information
        for text in paragraph_texts:
            text_lower = text.lower()
            if any(date_word in text_lower for date_word in ['valid', 'date', 'period', 'until', 'from']):
                data["valid_dates"] = text
            
            if any(price_word in text_lower for price_word in ['price', 'cost', 'fee', 'discount', 'offer', 'save', 'usd', '$', 'nu']):
                data["price_info"] = text
        
        # Extract images
        images = await content_div.query_selector_all('img')
        for img in images:
            src = await img.get_attribute('src')
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

async def main():
    """Main function to process all URLs"""
    logger.info("Starting extraction process with Playwright")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Process each category
        for category, urls in URLS.items():
            logger.info(f"Processing category: {category}")
            category_items = []
            
            for url in urls:
                # Get the slug from the URL
                path = urlparse(url).path
                slug = path.strip('/').split('/')[-1]
                
                # Extract data
                data = await extract_url_data(page, url, category)
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
                        summary["tours_count"] = len(data.get("tours", []))
                    elif category == "festivals" and "festivals" in data:
                        summary["festivals_count"] = len(data.get("festivals", []))
                    elif category == "trekking" and "treks" in data:
                        summary["treks_count"] = len(data.get("treks", []))
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
                await asyncio.sleep(1)
            
            # Create category index file
            create_category_index(category, category_items)
        
        # Close browser
        await browser.close()
    
    logger.info("Extraction process completed")

if __name__ == "__main__":
    asyncio.run(main()) 