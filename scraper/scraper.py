"""
Main scraper functionality for extracting data from the Breathe Bhutan website.
"""
import os
import json
import time
import asyncio
from typing import Dict, List, Any
from playwright.async_api import async_playwright
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm

import config
from utils.logger import get_logger

logger = get_logger("scraper")

class BhutanScraper:
    """
    Scraper for extracting tour data from the Breathe Bhutan website.
    """
    
    def __init__(self, base_url=config.BASE_URL):
        """
        Initialize the scraper.
        
        Args:
            base_url (str): Base URL of the website to scrape
        """
        self.base_url = base_url
        
        # Ensure data directory exists
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        logger.info(f"Scraper initialized with base URL: {base_url}")
    
    async def _setup_browser(self):
        """
        Set up a Playwright browser for scraping.
        
        Returns:
            tuple: Playwright, Browser, and Page objects
        """
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        return playwright, browser, page
    
    async def _make_request(self, url):
        """
        Make a request to the given URL with error handling and retries.
        
        Args:
            url (str): URL to request
            
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        full_url = urljoin(self.base_url, url)
        logger.debug(f"Making request to: {full_url}")
        
        max_retries = 3
        retry_delay = 2
        
        playwright, browser, page = await self._setup_browser()
        
        try:
            for attempt in range(max_retries):
                try:
                    await page.goto(full_url, wait_until='networkidle')
                    content = await page.content()
                    
                    logger.debug(f"Request successful: {full_url}")
                    return BeautifulSoup(content, 'html.parser')
                
                except Exception as e:
                    logger.error(f"Request error ({attempt+1}/{max_retries}): {str(e)}")
                    
                    if attempt < max_retries - 1:
                        logger.debug(f"Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Failed to fetch {full_url} after {max_retries} attempts")
                        raise
        finally:
            await browser.close()
            await playwright.stop()
    
    async def scrape_homepage(self):
        """
        Scrape the homepage to get basic information and navigation links.
        
        Returns:
            dict: Homepage data including testimonials and overview
        """
        logger.info("Scraping homepage")
        soup = await self._make_request("/")
        
        homepage_data = {
            'testimonials': [],
            'overview': '',
            'navigation_links': []
        }
        
        try:
            # Extract testimonials
            testimonial_items = soup.select('.testimonial-item')
            for item in testimonial_items:
                try:
                    reviewer_name = item.select_one('.reviewer-name').text.strip()
                    review_date = item.select_one('.review-date').text.strip()
                    review_text = item.select_one('.review-text').text.strip()
                    
                    homepage_data['testimonials'].append({
                        'name': reviewer_name,
                        'date': review_date,
                        'text': review_text
                    })
                except Exception as e:
                    logger.error(f"Error extracting testimonial: {str(e)}")
            
            # Extract company overview
            overview_section = soup.select_one('.company-overview')
            if overview_section:
                homepage_data['overview'] = overview_section.text.strip()
            
            # Extract navigation links
            nav_items = soup.select('nav a')
            for nav in nav_items:
                try:
                    link_text = nav.text.strip()
                    link_url = nav.get('href', '')
                    
                    homepage_data['navigation_links'].append({
                        'text': link_text,
                        'url': urljoin(self.base_url, link_url)
                    })
                except Exception as e:
                    logger.error(f"Error extracting navigation link: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error scraping homepage: {str(e)}")
        
        # Save data to file
        self._save_data(homepage_data, os.path.join(config.DATA_DIR, "homepage.json"))
        logger.info("Homepage data saved")
        
        return homepage_data
    
    async def scrape_cultural_tours(self):
        """
        Scrape cultural tours data.
        
        Returns:
            list: List of cultural tour data
        """
        logger.info("Scraping cultural tours")
        
        # Since the structure might be different from what we initially expected,
        # Let's extract tour information from the reviews section since it contains
        # actual tour experience details
        tours = []
        
        try:
            # First try to get data from the cultural tours page
            soup = await self._make_request("/cultural-tours/")
            
            # If that fails, extract from reviews
            if not soup or soup.select('.review-item'):
                soup = await self._make_request("/reviews/")
            
            # Find all review/tour items on the page
            review_items = soup.select('.review-item') or soup.select('.testimonial')
            
            for item in tqdm(review_items, desc="Processing cultural tours"):
                try:
                    # Extract relevant information
                    reviewer = item.select_one('.reviewer-name')
                    reviewer_name = reviewer.text.strip() if reviewer else "Anonymous"
                    
                    review_text = item.select_one('.review-text, .testimonial-text')
                    full_text = review_text.text.strip() if review_text else ""
                    
                    # Extract what appears to be tour details from the review
                    tour_data = {
                        'title': f"Cultural experience mentioned by {reviewer_name}",
                        'description': full_text[:200] + "..." if len(full_text) > 200 else full_text,
                        'full_description': full_text,
                        'reviewer': reviewer_name,
                        'category': 'cultural',
                        'highlights': self._extract_highlights_from_text(full_text),
                        'source': 'review'
                    }
                    
                    # Try to extract duration
                    duration_match = self._extract_duration_from_text(full_text)
                    if duration_match:
                        tour_data['duration'] = duration_match
                    
                    tours.append(tour_data)
                    logger.debug(f"Extracted tour from review by: {reviewer_name}")
                    
                except Exception as e:
                    logger.error(f"Error extracting tour from review: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping cultural tours: {str(e)}")
        
        # Save data to file
        self._save_data(tours, config.TOURS_FILE)
        logger.info(f"Scraped {len(tours)} cultural tours")
        
        return tours
    
    async def scrape_festivals(self):
        """
        Scrape festivals data.
        
        Returns:
            list: List of festival data
        """
        logger.info("Scraping festivals")
        
        festivals = []
        
        try:
            # Try to access festivals page
            soup = await self._make_request("/festivals/")
            
            # Find all festival items on the page
            festival_items = soup.select('.festival-item') or soup.select('.event-item')
            
            if not festival_items:
                # If no specific festival selectors are found, look for content blocks that might describe festivals
                content_blocks = soup.select('.content-block, .event-block, article, .blog-post')
                
                for block in tqdm(content_blocks, desc="Processing festival content"):
                    try:
                        title_elem = block.select_one('h1, h2, h3, .title')
                        title = title_elem.text.strip() if title_elem else "Bhutanese Festival"
                        
                        description_elem = block.select_one('p, .description, .content')
                        description = description_elem.text.strip() if description_elem else ""
                        
                        if any(keyword in title.lower() or keyword in description.lower() 
                               for keyword in ['festival', 'tshechu', 'celebration', 'traditional', 'ceremony']):
                            
                            festival_data = {
                                'title': title,
                                'description': description,
                                'category': 'festival',
                                'highlights': self._extract_highlights_from_text(description),
                                'source': 'content'
                            }
                            
                            festivals.append(festival_data)
                            logger.debug(f"Extracted festival: {title}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting festival from content block: {str(e)}")
            else:
                # Process specific festival items if they exist
                for item in tqdm(festival_items, desc="Processing festivals"):
                    try:
                        title = item.select_one('.festival-name, .event-name, h3').text.strip()
                        description = item.select_one('.festival-description, .event-description, p').text.strip()
                        
                        # Try to extract date information
                        date_elem = item.select_one('.festival-date, .event-date, .date')
                        date = date_elem.text.strip() if date_elem else "Annual festival"
                        
                        festival_data = {
                            'title': title,
                            'description': description,
                            'date': date,
                            'category': 'festival',
                            'source': 'festival'
                        }
                        
                        festivals.append(festival_data)
                        logger.debug(f"Extracted festival: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting festival: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping festivals: {str(e)}")
        
        # Save data to file
        self._save_data(festivals, config.FESTIVALS_FILE)
        logger.info(f"Scraped {len(festivals)} festivals")
        
        return festivals
    
    async def scrape_trekking(self):
        """
        Scrape trekking options.
        
        Returns:
            list: List of trekking data
        """
        logger.info("Scraping trekking options")
        
        trekking_options = []
        
        try:
            # Try to access trekking page
            soup = await self._make_request("/trekking/")
            
            # Find all trekking items on the page
            trek_items = soup.select('.trek-item') or soup.select('.tour-item')
            
            if not trek_items:
                # Look for blog posts or reviews that might mention trekking
                content_blocks = soup.select('article, .blog-post, .review-item, .testimonial')
                
                for block in tqdm(content_blocks, desc="Processing trekking content"):
                    try:
                        text_content = block.text.strip()
                        
                        if any(keyword in text_content.lower() 
                               for keyword in ['trek', 'hiking', 'trail', 'mountain', 'hike', 'walk']):
                            
                            title_elem = block.select_one('h1, h2, h3, .title, strong')
                            title = title_elem.text.strip() if title_elem else "Bhutan Trekking Experience"
                            
                            description_elem = block.select_one('p, .description, .content, .text')
                            description = description_elem.text.strip() if description_elem else text_content
                            
                            trek_data = {
                                'title': title,
                                'description': description,
                                'category': 'trekking',
                                'highlights': self._extract_highlights_from_text(text_content),
                                'difficulty': self._extract_difficulty_from_text(text_content),
                                'source': 'content'
                            }
                            
                            # Try to extract duration
                            duration_match = self._extract_duration_from_text(text_content)
                            if duration_match:
                                trek_data['duration'] = duration_match
                            
                            trekking_options.append(trek_data)
                            logger.debug(f"Extracted trekking option: {title}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting trekking option from content: {str(e)}")
            else:
                # Process specific trekking items if they exist
                for item in tqdm(trek_items, desc="Processing trekking options"):
                    try:
                        title = item.select_one('.trek-name, .tour-name, h3').text.strip()
                        description = item.select_one('.trek-description, .tour-description, p').text.strip()
                        
                        # Try to extract duration
                        duration_elem = item.select_one('.trek-duration, .tour-duration, .duration')
                        duration = duration_elem.text.strip() if duration_elem else "Multi-day trek"
                        
                        # Try to extract difficulty
                        difficulty_elem = item.select_one('.trek-difficulty, .difficulty-level')
                        difficulty = difficulty_elem.text.strip() if difficulty_elem else "Varied"
                        
                        trek_data = {
                            'title': title,
                            'description': description,
                            'duration': duration,
                            'difficulty': difficulty,
                            'category': 'trekking',
                            'source': 'trek'
                        }
                        
                        trekking_options.append(trek_data)
                        logger.debug(f"Extracted trekking option: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting trekking option: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping trekking options: {str(e)}")
        
        # Save data to file
        self._save_data(trekking_options, config.TREKKING_FILE)
        logger.info(f"Scraped {len(trekking_options)} trekking options")
        
        return trekking_options
    
    async def scrape_itineraries(self):
        """
        Scrape pre-designed itineraries.
        
        Returns:
            list: List of itinerary data
        """
        logger.info("Scraping itineraries")
        
        itineraries = []
        
        try:
            # Try to access itineraries page
            soup = await self._make_request("/itineraries/")
            
            # Try alternate pages if the primary one doesn't work
            if not soup or not soup.select('.itinerary-item'):
                soup = await self._make_request("/tours/")
            
            if not soup or not soup.select('.itinerary-item'):
                soup = await self._make_request("/about-us/")
            
            # Find all itinerary items on the page
            itinerary_items = soup.select('.itinerary-item') or soup.select('.tour-item')
            
            if not itinerary_items:
                # Look for content that might describe itineraries
                content_blocks = soup.select('article, .content-block, .tour-block')
                
                for block in tqdm(content_blocks, desc="Processing itinerary content"):
                    try:
                        text_content = block.text.strip()
                        
                        if any(keyword in text_content.lower() 
                               for keyword in ['day', 'itinerary', 'schedule', 'plan', 'tour']):
                            
                            title_elem = block.select_one('h1, h2, h3, .title')
                            title = title_elem.text.strip() if title_elem else "Bhutan Travel Itinerary"
                            
                            description_elem = block.select_one('p, .description, .content')
                            description = description_elem.text.strip() if description_elem else text_content[:500]
                            
                            # Extract what seems to be daily itinerary items
                            day_elems = block.select('h4, h5, strong, .day-title')
                            daily_items = []
                            
                            for day_elem in day_elems:
                                day_text = day_elem.text.strip()
                                if any(day_marker in day_text.lower() for day_marker in ['day', 'morning', 'afternoon', 'evening']):
                                    # Find the description for this day
                                    day_description = ""
                                    next_elem = day_elem.find_next('p')
                                    if next_elem:
                                        day_description = next_elem.text.strip()
                                    
                                    daily_items.append({
                                        'title': day_text,
                                        'description': day_description
                                    })
                            
                            itinerary_data = {
                                'title': title,
                                'description': description,
                                'category': 'itinerary',
                                'itinerary': daily_items if daily_items else self._extract_itinerary_from_text(text_content),
                                'source': 'content'
                            }
                            
                            # Try to extract duration
                            duration_match = self._extract_duration_from_text(text_content)
                            if duration_match:
                                itinerary_data['duration'] = duration_match
                            
                            itineraries.append(itinerary_data)
                            logger.debug(f"Extracted itinerary: {title}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting itinerary from content: {str(e)}")
            else:
                # Process specific itinerary items if they exist
                for item in tqdm(itinerary_items, desc="Processing itineraries"):
                    try:
                        title = item.select_one('.itinerary-name, .tour-name, h3').text.strip()
                        description = item.select_one('.itinerary-description, .tour-description, p').text.strip()
                        
                        # Try to extract duration
                        duration_elem = item.select_one('.itinerary-duration, .tour-duration, .duration')
                        duration = duration_elem.text.strip() if duration_elem else "Multi-day tour"
                        
                        # Try to extract daily itinerary items
                        day_items = item.select('.day-item, .itinerary-day')
                        daily_items = []
                        
                        for day_item in day_items:
                            day_title = day_item.select_one('.day-title, h4').text.strip()
                            day_description = day_item.select_one('.day-description, p').text.strip()
                            
                            daily_items.append({
                                'title': day_title,
                                'description': day_description
                            })
                        
                        itinerary_data = {
                            'title': title,
                            'description': description,
                            'duration': duration,
                            'itinerary': daily_items,
                            'category': 'itinerary',
                            'source': 'itinerary'
                        }
                        
                        itineraries.append(itinerary_data)
                        logger.debug(f"Extracted itinerary: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting itinerary: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping itineraries: {str(e)}")
        
        # Save data to file
        self._save_data(itineraries, config.ITINERARIES_FILE)
        logger.info(f"Scraped {len(itineraries)} itineraries")
        
        return itineraries
    
    async def scrape_reviews(self):
        """
        Scrape customer reviews.
        
        Returns:
            list: List of review data
        """
        logger.info("Scraping reviews")
        
        reviews = []
        
        try:
            # Access reviews page
            soup = await self._make_request("/reviews/")
            
            # Find all review items
            review_items = soup.select('.review-item, .testimonial')
            
            for item in tqdm(review_items, desc="Processing reviews"):
                try:
                    # Extract reviewer information
                    reviewer_elem = item.select_one('.reviewer-name, .author')
                    reviewer = reviewer_elem.text.strip() if reviewer_elem else "Anonymous"
                    
                    # Extract review content
                    content_elem = item.select_one('.review-text, .testimonial-text, .content, p')
                    content = content_elem.text.strip() if content_elem else ""
                    
                    # Extract date if available
                    date_elem = item.select_one('.review-date, .date')
                    date = date_elem.text.strip() if date_elem else ""
                    
                    # Extract rating if available
                    rating_elem = item.select_one('.rating, .stars')
                    rating = rating_elem.text.strip() if rating_elem else "5/5"
                    
                    review_data = {
                        'reviewer': reviewer,
                        'content': content,
                        'date': date,
                        'rating': rating
                    }
                    
                    reviews.append(review_data)
                    logger.debug(f"Extracted review from: {reviewer}")
                    
                except Exception as e:
                    logger.error(f"Error extracting review: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping reviews: {str(e)}")
        
        # Save data to file
        self._save_data(reviews, os.path.join(config.DATA_DIR, "reviews.json"))
        logger.info(f"Scraped {len(reviews)} reviews")
        
        return reviews
    
    def _extract_highlights_from_text(self, text):
        """
        Extract potential highlights from text content.
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            list: Extracted highlights
        """
        highlights = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith('•') or line.startswith('-') or line.startswith('*') or (line and line[0].isdigit() and line[1:3] in ['. ', ') ']):
                highlights.append(line)
            elif len(line) > 15 and len(line) < 100 and ('.' not in line or line.count('.') == 1):
                # Sentences that look like highlights (short and meaningful)
                highlights.append(line)
        
        # If no clear highlights, create some from sentences
        if not highlights and len(text) > 50:
            sentences = text.split('.')
            for sentence in sentences[:5]:  # Use first 5 sentences
                sentence = sentence.strip()
                if len(sentence) > 15 and len(sentence) < 100:
                    highlights.append(sentence)
        
        # Limit to top 5 highlights
        return highlights[:5]
    
    def _extract_duration_from_text(self, text):
        """
        Extract duration information from text.
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            str: Extracted duration or None
        """
        import re
        
        # Look for patterns like "3 days", "10-day", "7-day tour", etc.
        day_patterns = [
            r'(\d+)[\s-]day',
            r'(\d+)[\s-]days',
            r'tour of (\d+) days',
            r'for (\d+) days'
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                days = match.group(1)
                return f"{days} days"
        
        return None
    
    def _extract_difficulty_from_text(self, text):
        """
        Extract difficulty level from trekking text.
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            str: Difficulty level
        """
        text_lower = text.lower()
        
        if 'easy' in text_lower:
            return 'Easy'
        elif 'moderate' in text_lower:
            return 'Moderate'
        elif 'challenging' in text_lower or 'difficult' in text_lower:
            return 'Challenging'
        elif 'strenuous' in text_lower or 'hard' in text_lower:
            return 'Strenuous'
        
        return 'Varied'
    
    def _extract_itinerary_from_text(self, text):
        """
        Extract daily itinerary items from text.
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            list: List of daily itinerary items
        """
        import re
        
        itinerary_items = []
        
        # Look for day patterns
        day_patterns = [
            r'Day (\d+)[:\-]([^\n]+)',
            r'Day (\d+)\.([^\n]+)',
            r'(\d+)st day[:\-]([^\n]+)',
            r'(\d+)nd day[:\-]([^\n]+)',
            r'(\d+)rd day[:\-]([^\n]+)',
            r'(\d+)th day[:\-]([^\n]+)'
        ]
        
        for pattern in day_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                day_num = match[0]
                description = match[1].strip()
                
                itinerary_items.append({
                    'title': f"Day {day_num}",
                    'description': description
                })
        
        # If no clear day patterns found, try to split by common markers
        if not itinerary_items:
            sections = re.split(r'\n\n|\r\n\r\n', text)
            for i, section in enumerate(sections[:7]):  # Limit to 7 days
                if len(section.strip()) > 20:
                    itinerary_items.append({
                        'title': f"Day {i+1}",
                        'description': section.strip()
                    })
        
        return itinerary_items
    
    def _save_data(self, data, file_path):
        """
        Save scraped data to a JSON file.
        
        Args:
            data (list or dict): Data to save
            file_path (str): Path to save the data to
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {str(e)}")
    
    async def run_scraper(self):
        """
        Run the complete scraping process.
        
        This method orchestrates the scraping of all sections of the website.
        """
        try:
            logger.info("Starting scraper for Breathe Bhutan website")
            
            # Scrape homepage for basic site information
            homepage_data = await self.scrape_homepage()
            self._save_data(homepage_data, os.path.join(config.DATA_DIR, "homepage.json"))
            logger.info("Homepage data saved successfully")
            
            # Scrape cultural tours information
            cultural_tours = await self.scrape_cultural_tours()
            self._save_data(cultural_tours, config.TOURS_FILE)
            logger.info("Cultural tours data saved successfully")
            
            # Scrape festivals information
            festivals = await self.scrape_festivals()
            self._save_data(festivals, config.FESTIVALS_FILE)
            logger.info("Festivals data saved successfully")
            
            # Scrape trekking information
            trekking = await self.scrape_trekking()
            self._save_data(trekking, config.TREKKING_FILE)
            logger.info("Trekking data saved successfully")
            
            # Scrape itineraries information
            itineraries = await self.scrape_itineraries()
            self._save_data(itineraries, config.ITINERARIES_FILE)
            logger.info("Itineraries data saved successfully")
            
            # Scrape testimonials/reviews
            reviews = await self.scrape_reviews()
            self._save_data(reviews, os.path.join(config.DATA_DIR, "testimonials.json"))
            logger.info("Reviews data saved successfully")
            
            # Scrape contact and about information
            about_data = await self.scrape_about_page()
            self._save_data(about_data, os.path.join(config.DATA_DIR, "about.json"))
            logger.info("About page data saved successfully")
            
            # Scrape FAQ and visa information
            faq_data = await self.scrape_faq_page()
            self._save_data(faq_data, os.path.join(config.DATA_DIR, "faq.json"))
            logger.info("FAQ data saved successfully")
            
            # Scrape Bhutan travel guide
            travel_guide = await self.scrape_travel_guide()
            self._save_data(travel_guide, os.path.join(config.DATA_DIR, "travel_guide.json"))
            logger.info("Travel guide data saved successfully")
            
            # Scrape Bhutan regions information
            regions_data = await self.scrape_regions()
            self._save_data(regions_data, os.path.join(config.DATA_DIR, "regions.json"))
            logger.info("Regions data saved successfully")
            
            # Create a comprehensive general info with everything combined
            general_info = self._create_comprehensive_general_info()
            self._save_data(general_info, os.path.join(config.DATA_DIR, "general_info.json"))
            logger.info("Comprehensive general info saved successfully")
            
            logger.info("All data scraped and saved successfully")
        
        except Exception as e:
            logger.error(f"Error during scraping process: {str(e)}")
            raise
    
    async def scrape_about_page(self):
        """
        Scrape the About page for company information and contact details.
        
        Returns:
            dict: Information about Breathe Bhutan company
        """
        logger.info("Scraping About page")
        
        try:
            about_url = urljoin(self.base_url, "/about-us/")
            html = await self._make_request(about_url)
            
            if not html:
                logger.error("Failed to get About page")
                return {}
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize data structure
            about_data = {
                "company_name": "Breathe Bhutan",
                "about_sections": [],
                "team_members": [],
                "contact_info": {}
            }
            
            # Extract main content
            content_sections = soup.select('.entry-content > div')
            for section in content_sections:
                section_title = section.find('h2')
                section_text = section.find_all(['p', 'li'])
                
                if section_title:
                    section_data = {
                        "title": section_title.get_text(strip=True),
                        "content": "\n".join([p.get_text(strip=True) for p in section_text])
                    }
                    about_data["about_sections"].append(section_data)
            
            # Extract team members if available
            team_sections = soup.select('.team-member')
            for member in team_sections:
                member_name = member.select_one('.team-member-name')
                member_role = member.select_one('.team-member-role')
                member_bio = member.select_one('.team-member-bio')
                
                if member_name:
                    member_data = {
                        "name": member_name.get_text(strip=True) if member_name else "",
                        "role": member_role.get_text(strip=True) if member_role else "",
                        "bio": member_bio.get_text(strip=True) if member_bio else ""
                    }
                    about_data["team_members"].append(member_data)
            
            # Extract contact information
            contact_section = soup.select_one('.contact-info')
            if contact_section:
                email = contact_section.select_one('a[href^="mailto:"]')
                phone = contact_section.select_one('a[href^="tel:"]')
                address = contact_section.select_one('.address')
                
                about_data["contact_info"] = {
                    "email": email.get_text(strip=True) if email else "",
                    "phone": phone.get_text(strip=True) if phone else "",
                    "address": address.get_text(strip=True) if address else ""
                }
            
            return about_data
        
        except Exception as e:
            logger.error(f"Error scraping About page: {str(e)}")
            return {}
    
    async def scrape_faq_page(self):
        """
        Scrape the FAQ page for frequently asked questions and visa information.
        
        Returns:
            dict: FAQ and visa information
        """
        logger.info("Scraping FAQ page")
        
        try:
            faq_url = urljoin(self.base_url, "/faq/")
            html = await self._make_request(faq_url)
            
            if not html:
                logger.error("Failed to get FAQ page")
                return {}
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize data structure
            faq_data = {
                "general_faqs": [],
                "visa_information": [],
                "travel_requirements": []
            }
            
            # Extract FAQ sections
            faq_sections = soup.select('.faq-section, .entry-content > div')
            
            for section in faq_sections:
                section_title = section.find(['h2', 'h3'])
                questions = section.select('.faq-question, .wp-block-heading')
                
                # Process each question in the section
                current_category = "general_faqs"
                if section_title:
                    title_text = section_title.get_text(strip=True).lower()
                    if "visa" in title_text:
                        current_category = "visa_information"
                    elif "requirement" in title_text:
                        current_category = "travel_requirements"
                
                # Process questions and answers
                for q in questions:
                    question_text = q.get_text(strip=True)
                    answer = ""
                    
                    # Find answer in the next sibling paragraphs
                    next_el = q.find_next(['p', 'ul', 'ol'])
                    while next_el and next_el.name in ['p', 'ul', 'ol'] and next_el.name != 'h2' and next_el.name != 'h3':
                        if next_el.name == 'ul' or next_el.name == 'ol':
                            items = next_el.find_all('li')
                            answer += "\n".join([f"- {item.get_text(strip=True)}" for item in items])
                        else:
                            answer += next_el.get_text(strip=True) + "\n"
                        next_el = next_el.find_next_sibling()
                    
                    faq_item = {
                        "question": question_text,
                        "answer": answer.strip()
                    }
                    
                    faq_data[current_category].append(faq_item)
            
            return faq_data
        
        except Exception as e:
            logger.error(f"Error scraping FAQ page: {str(e)}")
            return {}
    
    async def scrape_travel_guide(self):
        """
        Scrape the Travel Guide for general information about Bhutan.
        
        Returns:
            dict: Travel guide information
        """
        logger.info("Scraping Travel Guide")
        
        try:
            guide_url = urljoin(self.base_url, "/bhutan-travel-guide/")
            html = await self._make_request(guide_url)
            
            if not html:
                logger.error("Failed to get Travel Guide page")
                return {}
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize data structure
            guide_data = {
                "travel_guide_sections": [],
                "culture_info": [],
                "geography": {},
                "climate": {},
                "best_time_to_visit": "",
                "practical_info": []
            }
            
            # Extract main content sections
            content_sections = soup.select('.entry-content > div, .guide-section')
            
            for section in content_sections:
                section_title = section.find(['h2', 'h3'])
                section_text = section.find_all(['p', 'li'])
                
                if section_title:
                    title_text = section_title.get_text(strip=True)
                    content = "\n".join([p.get_text(strip=True) for p in section_text])
                    
                    section_data = {
                        "title": title_text,
                        "content": content
                    }
                    
                    # Categorize the section based on title
                    title_lower = title_text.lower()
                    if "culture" in title_lower or "tradition" in title_lower:
                        guide_data["culture_info"].append(section_data)
                    elif "geography" in title_lower or "landscape" in title_lower:
                        guide_data["geography"] = section_data
                    elif "climate" in title_lower or "weather" in title_lower:
                        guide_data["climate"] = section_data
                    elif "best time" in title_lower or "when to visit" in title_lower:
                        guide_data["best_time_to_visit"] = content
                    elif any(word in title_lower for word in ["passport", "visa", "money", "currency", "language", "health", "safety"]):
                        guide_data["practical_info"].append(section_data)
                    else:
                        guide_data["travel_guide_sections"].append(section_data)
            
            return guide_data
        
        except Exception as e:
            logger.error(f"Error scraping Travel Guide: {str(e)}")
            return {}
    
    async def scrape_regions(self):
        """
        Scrape information about different regions of Bhutan.
        
        Returns:
            dict: Information about Bhutan's regions
        """
        logger.info("Scraping Regions information")
        
        try:
            regions_url = urljoin(self.base_url, "/regions-of-bhutan/")
            html = await self._make_request(regions_url)
            
            if not html:
                # Try alternative URL structure
                regions_url = urljoin(self.base_url, "/destinations/")
                html = await self._make_request(regions_url)
                
                if not html:
                    logger.error("Failed to get Regions page")
                    return {}
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize data structure
            regions_data = {
                "regions": []
            }
            
            # Extract region sections
            region_sections = soup.select('.region-section, .destination-card, .entry-content > div')
            
            for section in region_sections:
                region_name = section.find(['h2', 'h3', '.region-name'])
                region_desc = section.find_all(['p'])
                region_img = section.find('img')
                
                if region_name:
                    region_data = {
                        "name": region_name.get_text(strip=True),
                        "description": "\n".join([p.get_text(strip=True) for p in region_desc]),
                        "image_url": region_img['src'] if region_img and 'src' in region_img.attrs else "",
                        "attractions": []
                    }
                    
                    # Extract attractions if available
                    attractions = section.select('.attraction, li')
                    for attraction in attractions:
                        attraction_name = attraction.find(['h4', 'strong']) or attraction
                        
                        if attraction_name:
                            attraction_data = {
                                "name": attraction_name.get_text(strip=True),
                                "description": attraction.get_text(strip=True) if attraction != attraction_name else ""
                            }
                            region_data["attractions"].append(attraction_data)
                    
                    regions_data["regions"].append(region_data)
            
            return regions_data
        
        except Exception as e:
            logger.error(f"Error scraping Regions information: {str(e)}")
            return {}
    
    def _create_comprehensive_general_info(self):
        """
        Create a comprehensive general information dictionary combining all scraped data.
        
        Returns:
            dict: Comprehensive information about Bhutan for general reference
        """
        logger.info("Creating comprehensive general information")
        
        try:
            # Initialize the comprehensive info dict
            general_info = {
                "country_name": "Bhutan",
                "official_name": "Kingdom of Bhutan",
                "description": "A small Himalayan kingdom known for its Gross National Happiness philosophy, stunning landscapes, and preserved traditions.",
                "capital": "Thimphu",
                "language": "Dzongkha (official), English (widely used), plus various regional dialects",
                "currency": "Ngultrum (BTN)",
                "religion": "Buddhism (predominantly Vajrayana Buddhism)",
                "tour_categories": [],
                "popular_destinations": [],
                "visa_requirements": {},
                "best_time_to_visit": {},
                "practical_information": {},
                "contact_information": {}
            }
            
            # Try to load existing data files to consolidate information
            try:
                # Load travel guide data
                travel_guide_path = os.path.join(config.DATA_DIR, "travel_guide.json")
                if os.path.exists(travel_guide_path):
                    with open(travel_guide_path, 'r', encoding='utf-8') as f:
                        travel_guide = json.load(f)
                    
                    # Extract best time to visit
                    general_info["best_time_to_visit"] = {
                        "description": travel_guide.get("best_time_to_visit", ""),
                        "seasons": {
                            "spring": "March to May - Mild temperatures and beautiful blooming flowers",
                            "summer": "June to August - Monsoon season with lush green landscapes",
                            "autumn": "September to November - Clear skies and pleasant weather, ideal for trekking",
                            "winter": "December to February - Cold but clear days, perfect for bird watching and cultural tours"
                        }
                    }
                    
                    # Extract practical information
                    practical_items = travel_guide.get("practical_info", [])
                    for item in practical_items:
                        category = item.get("title", "").lower()
                        if "currency" in category or "money" in category:
                            general_info["practical_information"]["currency"] = item.get("content", "")
                        elif "language" in category:
                            general_info["practical_information"]["language"] = item.get("content", "")
                        elif "health" in category:
                            general_info["practical_information"]["health"] = item.get("content", "")
                        elif "safety" in category:
                            general_info["practical_information"]["safety"] = item.get("content", "")
                        else:
                            general_info["practical_information"][category] = item.get("content", "")
                
                # Load FAQ and visa data
                faq_path = os.path.join(config.DATA_DIR, "faq.json")
                if os.path.exists(faq_path):
                    with open(faq_path, 'r', encoding='utf-8') as f:
                        faq_data = json.load(f)
                    
                    # Extract visa requirements
                    visa_faqs = faq_data.get("visa_information", [])
                    if visa_faqs:
                        general_info["visa_requirements"] = {
                            "process": "",
                            "documents_needed": [],
                            "fees": "",
                            "processing_time": ""
                        }
                        
                        for faq in visa_faqs:
                            question = faq.get("question", "").lower()
                            answer = faq.get("answer", "")
                            
                            if "process" in question or "how to" in question:
                                general_info["visa_requirements"]["process"] = answer
                            elif "document" in question or "need" in question:
                                general_info["visa_requirements"]["documents_needed"] = self._extract_list_items(answer)
                            elif "fee" in question or "cost" in question:
                                general_info["visa_requirements"]["fees"] = answer
                            elif "time" in question or "long" in question:
                                general_info["visa_requirements"]["processing_time"] = answer
                
                # Load regions data
                regions_path = os.path.join(config.DATA_DIR, "regions.json")
                if os.path.exists(regions_path):
                    with open(regions_path, 'r', encoding='utf-8') as f:
                        regions_data = json.load(f)
                    
                    # Extract popular destinations
                    for region in regions_data.get("regions", []):
                        region_name = region.get("name", "")
                        attractions = region.get("attractions", [])
                        
                        destination = {
                            "name": region_name,
                            "description": region.get("description", ""),
                            "highlights": [attraction.get("name", "") for attraction in attractions]
                        }
                        
                        general_info["popular_destinations"].append(destination)
                
                # Load about data for contact information
                about_path = os.path.join(config.DATA_DIR, "about.json")
                if os.path.exists(about_path):
                    with open(about_path, 'r', encoding='utf-8') as f:
                        about_data = json.load(f)
                    
                    general_info["contact_information"] = about_data.get("contact_info", {})
                
                # Load tour categories
                for category_name, file_path in [
                    ("Cultural Tours", config.TOURS_FILE),
                    ("Festivals", config.FESTIVALS_FILE),
                    ("Trekking", config.TREKKING_FILE),
                    ("Itineraries", config.ITINERARIES_FILE)
                ]:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            category_data = json.load(f)
                        
                        category = {
                            "name": category_name,
                            "description": "",
                            "options_count": len(category_data),
                        }
                        
                        general_info["tour_categories"].append(category)
            
            except Exception as e:
                logger.error(f"Error loading data files for comprehensive info: {str(e)}")
            
            return general_info
        
        except Exception as e:
            logger.error(f"Error creating comprehensive general info: {str(e)}")
            return {}
    
    def _extract_list_items(self, text):
        """
        Extract list items from a text that might contain bullet points or numbered lists.
        
        Args:
            text (str): Text that may contain list items
            
        Returns:
            list: Extracted list items
        """
        # Split the text by common list item markers
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            # Check for bullet points or numbered list items
            if line.startswith('-') or line.startswith('•') or (line[0].isdigit() and line[1:3] in ['. ', ') ']):
                # Remove the bullet/number and add to items
                if line.startswith('-') or line.startswith('•'):
                    clean_line = line[1:].strip()
                else:
                    clean_line = line[line.find(' ')+1:].strip()
                
                if clean_line:
                    items.append(clean_line)
            elif line:  # If line has content but no list marker, it might be a continuation
                if items:
                    items[-1] += " " + line  # Append to the last item
                else:
                    items.append(line)  # Create a new item
        
        return items

if __name__ == "__main__":
    """
    Run the scraper as a standalone script.
    """
    scraper = BhutanScraper()
    asyncio.run(scraper.run_scraper()) 