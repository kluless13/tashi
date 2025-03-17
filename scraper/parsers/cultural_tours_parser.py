"""
Parser for cultural tours content from the Breathe Bhutan website.
"""
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.logger import get_logger

logger = get_logger("cultural_tours_parser")

class CulturalToursParser:
    """
    Parser for extracting cultural tours information from HTML content.
    """
    
    def __init__(self, base_url):
        """
        Initialize the parser.
        
        Args:
            base_url (str): Base URL of the website
        """
        self.base_url = base_url
    
    def parse_tours_list(self, soup):
        """
        Parse the main cultural tours list page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content of the tours list page
            
        Returns:
            list: Basic information about tours and their detail URLs
        """
        tours_list = []
        
        # Find all tour items on the page (adjust selector based on actual HTML structure)
        tour_items = soup.select('.tour-item')
        
        for item in tour_items:
            try:
                # Extract basic info from list page
                title = item.select_one('.tour-title').text.strip()
                summary = item.select_one('.tour-description').text.strip()
                
                # Try to extract duration and pricing information
                duration = item.select_one('.tour-duration')
                duration_text = duration.text.strip() if duration else "Duration not specified"
                
                pricing = item.select_one('.tour-pricing')
                pricing_text = pricing.text.strip() if pricing else "Pricing not specified"
                
                # Extract detail page URL
                detail_link = item.select_one('a.tour-link')
                if detail_link and 'href' in detail_link.attrs:
                    detail_url = detail_link['href']
                    full_detail_url = urljoin(self.base_url, detail_url)
                else:
                    logger.warning(f"No detail URL found for tour: {title}")
                    full_detail_url = None
                
                tour_basic_info = {
                    'title': title,
                    'summary': summary,
                    'duration': duration_text,
                    'pricing': pricing_text,
                    'detail_url': full_detail_url
                }
                
                tours_list.append(tour_basic_info)
                
            except Exception as e:
                logger.error(f"Error parsing tour item: {str(e)}")
        
        return tours_list
    
    def parse_tour_details(self, soup, basic_info):
        """
        Parse a cultural tour detail page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content of the tour detail page
            basic_info (dict): Basic information already extracted from the list page
            
        Returns:
            dict: Complete tour information
        """
        try:
            # Start with the basic info
            tour_data = basic_info.copy()
            
            # Extract detailed description
            description_elem = soup.select_one('.tour-description-full')
            if description_elem:
                tour_data['description'] = description_elem.text.strip()
            
            # Extract tour highlights
            highlights = []
            highlights_section = soup.select_one('.tour-highlights')
            if highlights_section:
                highlight_items = highlights_section.select('li')
                highlights = [item.text.strip() for item in highlight_items]
            tour_data['highlights'] = highlights
            
            # Extract itinerary
            tour_data['itinerary'] = self._extract_itinerary(soup)
            
            # Extract included/excluded items
            included = []
            included_section = soup.select_one('.tour-included')
            if included_section:
                included_items = included_section.select('li')
                included = [item.text.strip() for item in included_items]
            tour_data['included'] = included
            
            excluded = []
            excluded_section = soup.select_one('.tour-excluded')
            if excluded_section:
                excluded_items = excluded_section.select('li')
                excluded = [item.text.strip() for item in excluded_items]
            tour_data['excluded'] = excluded
            
            # Extract images
            images = []
            gallery_section = soup.select_one('.tour-gallery')
            if gallery_section:
                image_elements = gallery_section.select('img')
                for img in image_elements:
                    if 'src' in img.attrs:
                        image_url = urljoin(self.base_url, img['src'])
                        alt_text = img.get('alt', '')
                        images.append({
                            'url': image_url,
                            'alt': alt_text
                        })
            tour_data['images'] = images
            
            # Add metadata
            tour_data['category'] = 'cultural'
            
            return tour_data
            
        except Exception as e:
            logger.error(f"Error parsing tour details: {str(e)}")
            # Return basic info if there was an error parsing details
            return basic_info
    
    def _extract_itinerary(self, soup):
        """
        Extract itinerary details from a tour page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of daily itinerary items
        """
        itinerary_items = []
        
        # Find the itinerary section
        itinerary_section = soup.select_one('.tour-itinerary')
        if not itinerary_section:
            logger.warning("No itinerary section found")
            return itinerary_items
        
        # Find all day elements in the itinerary section
        day_elements = itinerary_section.select('.itinerary-day')
        
        for day_element in day_elements:
            try:
                # Extract day number/title
                day_title_elem = day_element.select_one('.day-title')
                day_title = day_title_elem.text.strip() if day_title_elem else "Day"
                
                # Extract day description
                day_desc_elem = day_element.select_one('.day-description')
                day_description = day_desc_elem.text.strip() if day_desc_elem else ""
                
                # Extract activities or points of interest
                activities = []
                activities_elem = day_element.select('.day-activity')
                for activity in activities_elem:
                    activities.append(activity.text.strip())
                
                # Extract accommodation details
                accommodation_elem = day_element.select_one('.day-accommodation')
                accommodation = accommodation_elem.text.strip() if accommodation_elem else "Not specified"
                
                # Extract meals included
                meals_elem = day_element.select_one('.day-meals')
                meals = meals_elem.text.strip() if meals_elem else "Not specified"
                
                itinerary_items.append({
                    'day': day_title,
                    'description': day_description,
                    'activities': activities,
                    'accommodation': accommodation,
                    'meals': meals
                })
                
            except Exception as e:
                logger.error(f"Error extracting itinerary day: {str(e)}")
        
        return itinerary_items 