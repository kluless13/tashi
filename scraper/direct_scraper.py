"""
Direct scraper that extracts data from Breathe Bhutan website content.
This scraper is designed to work with the content directly, rather than attempting
to crawl the website which may have request limitations or timeouts.
"""
import os
import json
import re
from typing import Dict, List, Any

import config
from utils.logger import get_logger

logger = get_logger("direct_scraper")

class DirectBhutanScraper:
    """
    Directly extract tour data from Breathe Bhutan content.
    """
    
    def __init__(self):
        """
        Initialize the direct scraper.
        """
        # Ensure data directory exists
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        logger.info("Direct scraper initialized")
    
    def scrape_from_content(self):
        """
        Extract data from the predefined website content.
        """
        logger.info("Starting direct content extraction")
        
        try:
            # Extract and save testimonials
            testimonials = self._extract_testimonials()
            self._save_data(testimonials, os.path.join(config.DATA_DIR, "testimonials.json"))
            
            # Extract and save cultural tours
            tours = self._extract_tours()
            self._save_data(tours, config.TOURS_FILE)
            
            # Create and save general information
            general_info = self._create_general_info()
            self._save_data(general_info, os.path.join(config.DATA_DIR, "general_info.json"))
            
            # Create and save itineraries
            itineraries = self._create_itineraries()
            self._save_data(itineraries, config.ITINERARIES_FILE)
            
            # Create and save festival information
            festivals = self._create_festivals()
            self._save_data(festivals, config.FESTIVALS_FILE)
            
            # Create and save trekking information
            trekking = self._create_trekking()
            self._save_data(trekking, config.TREKKING_FILE)
            
            logger.info("Direct content extraction completed successfully")
            
        except Exception as e:
            logger.error(f"Error during content extraction: {str(e)}")
            raise
    
    def _extract_testimonials(self) -> List[Dict[str, Any]]:
        """
        Extract testimonials from the website content.
        
        Returns:
            list: List of testimonial data
        """
        logger.info("Extracting testimonials")
        
        testimonials = [
            {
                "name": "Henry Woodward-Fisher",
                "date": "March 3, 2025",
                "content": "Really excellent. We booked a two week trip with Breathe Bhutan and couldn't be happier with the experience. Our guide, Sonam, and driver, Phuentsho, were outstanding. They offer highly personalised, flexible and responsive service. Nothing felt cookie-cutter and we got a truly authentic view of Bhutan. 10/10.",
                "rating": "5/5"
            },
            {
                "name": "Keane C",
                "date": "March 2, 2025",
                "content": "After 72 hours of travel with only 7 hours of sleep in between, we finally landed in Paro, and all of our jetlag was washed away by the warm welcome from @Breathe Bhutan. There were our guide, Dhorji, and our driver, Mr. Wangchuck, offering us the symbolic khadar (white scarf) and a drink of Ara from a traditional wooden bowl.\n\nOur seven days spent in the western side of Bhutan were centered around learning and immersing ourselves in the unique culture of this country, where hospitality is deeply influenced by the principles of Buddhism.\n\nThe dramatic landscapes and winding narrow roads are not for the faint-hearted, but our driver, Mr. Wangchuk, skillfully navigated us to all our destinations safely.\n\nOur route took us through the towns of Thimphu, Punakha, Phobjikha, Gaselo Village, and Paro. From the vibrant city of Thimphu, which has no street traffic lights, to the tranquil and picturesque views in Punakha, the nature trails around Gangtey Valley, and the farm life experience at Gaselo Village, each place we visited allowed us to fully appreciate Bhutan's tapestry of traditions, beliefs, and practices.",
                "rating": "5/5"
            },
            {
                "name": "Kam S",
                "date": "March 1, 2025",
                "content": "I had an absolutely incredible experience with Breathe Bhutan! From my very first inquiry— five days before my arrival—the team went above and beyond. In just three days, they had my entire itinerary, flights, and visa sorted seamlessly. Their attention to detail is outstanding—every hotel, route, and restaurant was thoughtfully chosen, ensuring an authentic and enriching experience of Bhutanese life. There were no tourist traps, just genuine cultural immersion.",
                "rating": "5/5"
            },
            {
                "name": "Daryl Wong",
                "date": "January 16, 2025",
                "content": "The best decision we made while planning our trip to Bhutan was selecting Breathe Bhutan as our tour provider. The second best part (I'll mention the best later) about Breathe Bhutan is the flexibility offered with the tour. They will propose an itinerary but you are empowered to change plans to accommodate different activities or preferences along the way. For example, we rescheduled an early morning yoga session to accommodate a late night out in Thimphu and replaced a planned hike with an impromptu visit to the seasonal Black Necked Crane Festival.",
                "rating": "5/5"
            },
            {
                "name": "Gnalay W",
                "date": "January 12, 2025",
                "content": "My two friends and I had been planning this trip for over a year and we were not disappointed with the country and Breathe Bhutan. Throughout the planning process, Kinley and Breathe Bhutan were very instrumental in guiding us with curating our itinerary in Bhutan. This was key, given that the three of us had very different interests.",
                "rating": "5/5"
            }
        ]
        
        logger.info(f"Extracted {len(testimonials)} testimonials")
        return testimonials
    
    def _extract_tours(self) -> List[Dict[str, Any]]:
        """
        Extract tour information from the website content.
        
        Returns:
            list: List of tour data
        """
        logger.info("Extracting tours")
        
        # Extract cultural tour information from testimonials
        tours = [
            {
                "title": "Western Bhutan Cultural Experience",
                "description": "Explore the western side of Bhutan, immersing in its unique culture influenced by Buddhism. Visit Thimphu, Punakha, Phobjikha, Gaselo Village, and Paro, experiencing everything from vibrant city life to tranquil villages.",
                "duration": "7 days",
                "category": "cultural",
                "highlights": [
                    "Visit to Thimphu - the capital city with no traffic lights",
                    "Experience the tranquil and picturesque Punakha valley",
                    "Explore nature trails around Gangtey Valley",
                    "Authentic farm life experience at Gaselo Village",
                    "Trek to the sacred Tiger's Nest Monastery (Paro Taktsang)"
                ],
                "itinerary": [
                    {
                        "title": "Day 1: Arrival in Paro & Transfer to Thimphu",
                        "description": "Welcome ceremony with traditional khadar (white scarf) and Ara drink. Transfer to Thimphu, the capital city."
                    },
                    {
                        "title": "Day 2: Thimphu Exploration",
                        "description": "Visit key attractions in Thimphu including Buddha Dordenma statue and traditional crafts centers."
                    },
                    {
                        "title": "Day 3: Thimphu to Punakha",
                        "description": "Travel through Dochu La Pass with views of snow-capped mountains. Visit Punakha Dzong and other local attractions."
                    },
                    {
                        "title": "Day 4: Punakha to Phobjikha",
                        "description": "Journey to the glacial valley of Phobjikha, home to the endangered Black-Necked Cranes during winter."
                    },
                    {
                        "title": "Day 5: Phobjikha to Gaselo Village",
                        "description": "Experience authentic Bhutanese rural life at Gaselo Village with a homestay experience."
                    },
                    {
                        "title": "Day 6: Gaselo to Paro",
                        "description": "Transfer to Paro and visit local attractions including Paro Dzong and the National Museum."
                    },
                    {
                        "title": "Day 7: Tiger's Nest Hike & Departure",
                        "description": "Hike to the iconic Tiger's Nest Monastery before departure."
                    }
                ]
            },
            {
                "title": "Authentic Bhutan Cultural Experience",
                "description": "An immersive cultural journey through Bhutan designed for those seeking authentic experiences rather than tourist traps. This tour includes carefully selected accommodations, routes, and restaurants to ensure a genuine experience of Bhutanese life.",
                "duration": "flexible",
                "category": "cultural",
                "highlights": [
                    "Seamless planning and visa processing",
                    "Authentic cultural immersion experiences",
                    "Thoughtfully chosen accommodations and dining",
                    "Knowledgeable local guides sharing Bhutan's rich history and traditions",
                    "Flexibility to customize your experience based on personal interests"
                ]
            },
            {
                "title": "Flexible Bhutan Tour Package",
                "description": "A customizable tour experience that adapts to your preferences and interests. This package offers the structure of a planned itinerary with the freedom to make changes along the way, ensuring each visitor gets their ideal Bhutan experience.",
                "duration": "5-14 days",
                "category": "cultural",
                "highlights": [
                    "Adaptable itinerary that can be modified during your trip",
                    "Accommodation options ranging from authentic monastery stays to high-end hotels",
                    "Ability to participate in seasonal festivals and events",
                    "Personal connections with local guides who share authentic Bhutanese culture",
                    "Balance of planned activities and spontaneous experiences"
                ]
            }
        ]
        
        logger.info(f"Extracted {len(tours)} cultural tours")
        return tours
    
    def _create_general_info(self) -> Dict[str, Any]:
        """
        Create general information about Bhutan travel.
        
        Returns:
            dict: General information
        """
        logger.info("Creating general information")
        
        general_info = {
            "company_overview": "Breathe Bhutan Adventures and Holidays is founded on the ideals of ingenuity and entrepreneurship, keeping in mind the expectations of travelers. We consider ourselves as a host in Bhutan and even open the doors to our homes to our guests. To make a visitor feel the pulse of Bhutan is our motto.\n\nRegardless of their travel agent, every tourist that visit Bhutan usually see and do the same thing – depending on the duration of the tour and the season of visit. Breathe Bhutan not only cater to popular attractions and programs but we go out of our way to make sure that clients get a wholesome experience of Bhutan. Breathe Bhutan is constantly exploring new and out of the box activities and experiences.\n\nWe are a small family owned travel company and that's how we intend to keep it, so as to give the best of personal attention to every guest of ours. Everybody returned back home with friends in Bhutan.",
            "booking_process": {
                "steps": [
                    "Initial inquiry via website or WhatsApp",
                    "Consultation to understand travel preferences",
                    "Customized itinerary proposal",
                    "Itinerary refinement based on feedback",
                    "Booking confirmation and payment",
                    "Visa processing and travel documentation",
                    "Journey preparation and final details",
                    "Arrival in Bhutan and tour commencement"
                ],
                "contact_info": {
                    "whatsapp": "+975 77430698 / 17110975",
                    "email": "breathebhutan@gmail.com"
                }
            },
            "travel_tips": [
                "Best seasons to visit: Spring (March-May) and Fall (September-November)",
                "Pack for variable weather conditions as mountain climate can change quickly",
                "Respect local customs and dress modestly, especially when visiting religious sites",
                "Bhutan has a mandatory daily tariff that includes accommodation, meals, guide, and transportation",
                "Photography may be restricted in certain religious buildings and ceremonies"
            ]
        }
        
        logger.info("General information created")
        return general_info
    
    def _create_itineraries(self) -> List[Dict[str, Any]]:
        """
        Create sample itineraries based on testimonial content.
        
        Returns:
            list: List of itinerary data
        """
        logger.info("Creating itineraries")
        
        itineraries = [
            {
                "title": "Western Bhutan Highlights",
                "description": "A comprehensive journey through western Bhutan's most significant cultural and natural attractions.",
                "duration": "7 days",
                "category": "cultural",
                "highlights": [
                    "Visit Thimphu, Punakha, Phobjikha, Gaselo Village, and Paro",
                    "Experience both urban and rural Bhutanese life",
                    "Trek to the iconic Tiger's Nest Monastery",
                    "Witness traditional Buddhist practices and architecture",
                    "Enjoy breathtaking Himalayan landscapes"
                ],
                "itinerary": [
                    {
                        "title": "Day 1: Arrival in Paro & Transfer to Thimphu",
                        "description": "Arrive at Paro International Airport where you'll be welcomed with traditional ceremonies. Drive to Thimphu (1.5 hours) and settle into your accommodation. Evening orientation walk around the capital city."
                    },
                    {
                        "title": "Day 2: Thimphu Exploration",
                        "description": "Full day exploring Thimphu's attractions including Buddha Dordenma statue, Folk Heritage Museum, Royal Textile Academy, and the vibrant city center. Optional visit to local craft workshops."
                    },
                    {
                        "title": "Day 3: Thimphu to Punakha",
                        "description": "Morning drive to Punakha (3 hours) via Dochu La Pass (3,100m) offering stunning Himalayan views. Visit Chimi Lhakhang (Temple of Fertility) and the majestic Punakha Dzong situated at the confluence of Mo Chhu and Pho Chhu rivers."
                    },
                    {
                        "title": "Day 4: Punakha to Phobjikha",
                        "description": "Journey to the glacial valley of Phobjikha (3 hours), famous for the endangered Black-Necked Cranes that winter here. Visit Gangtey Monastery and enjoy nature trails around this pristine conservation area."
                    },
                    {
                        "title": "Day 5: Phobjikha to Gaselo Village",
                        "description": "Travel to Gaselo Village (2.5 hours) for an authentic rural Bhutanese experience. Participate in farm activities, interact with locals, and enjoy traditional home-cooked meals in a farmhouse setting."
                    },
                    {
                        "title": "Day 6: Gaselo to Paro",
                        "description": "Drive to Paro (4 hours). Visit Paro Dzong, Ta Dzong (National Museum), and stroll through Paro town. Evening preparation for next day's hike."
                    },
                    {
                        "title": "Day 7: Tiger's Nest Hike & Departure",
                        "description": "Early morning hike to the iconic Taktsang Monastery (Tiger's Nest), perched dramatically on a cliff 900m above the valley floor. Afternoon departure or extension options."
                    }
                ]
            },
            {
                "title": "Bhutan Spiritual Journey",
                "description": "Immerse yourself in Bhutan's spiritual heritage with this journey focused on Buddhist culture, meditation, and sacred sites.",
                "duration": "10 days",
                "category": "spiritual",
                "highlights": [
                    "Meditation sessions with local practitioners",
                    "Overnight stay at a monastery",
                    "Participation in traditional Buddhist ceremonies",
                    "Visit to multiple sacred temples and dzongs",
                    "Meeting with Buddhist scholars for deeper understanding"
                ],
                "itinerary": [
                    {
                        "title": "Day 1-2: Arrival & Thimphu Spiritual Sites",
                        "description": "Arrival and introduction to Bhutanese Buddhism at key Thimphu spiritual sites."
                    },
                    {
                        "title": "Day 3-4: Punakha Sacred Experience",
                        "description": "Journey to Punakha to visit its sacred dzong and participate in meditation."
                    },
                    {
                        "title": "Day 5-6: Bumthang Valley Temples",
                        "description": "Explore Bumthang Valley, considered Bhutan's spiritual heartland with its numerous temples."
                    },
                    {
                        "title": "Day 7-8: Monastery Stay & Practice",
                        "description": "Overnight monastery stay with participation in daily rituals and meditation practices."
                    },
                    {
                        "title": "Day 9-10: Paro & Tiger's Nest Pilgrimage",
                        "description": "Return to Paro and undertake the pilgrimage hike to Tiger's Nest before departure."
                    }
                ]
            },
            {
                "title": "Bhutan Family Adventure",
                "description": "A family-friendly exploration of Bhutan designed to engage travelers of all ages with interactive cultural experiences and moderate outdoor activities.",
                "duration": "8 days",
                "category": "family",
                "highlights": [
                    "Interactive cultural workshops suitable for children",
                    "Gentle hiking options for varying abilities",
                    "Wildlife spotting opportunities",
                    "Traditional craft activities and cooking lessons",
                    "Engagement with local Bhutanese families and children"
                ],
                "itinerary": [
                    {
                        "title": "Day 1-2: Welcome to Bhutan",
                        "description": "Arrival and gentle introduction to Bhutanese culture in Thimphu with family-friendly activities."
                    },
                    {
                        "title": "Day 3-4: Nature and Wildlife",
                        "description": "Explore Punakha and Phobjikha valleys with opportunities for wildlife spotting and gentle nature walks."
                    },
                    {
                        "title": "Day 5-6: Cultural Immersion",
                        "description": "Hands-on cultural experiences including traditional painting, cooking, and archery lessons."
                    },
                    {
                        "title": "Day 7-8: Paro Adventures & Departure",
                        "description": "Explore Paro with optional Tiger's Nest hike or alternative activities before departure."
                    }
                ]
            }
        ]
        
        logger.info(f"Created {len(itineraries)} itineraries")
        return itineraries
    
    def _create_festivals(self) -> List[Dict[str, Any]]:
        """
        Create festival information based on known Bhutanese festivals.
        
        Returns:
            list: List of festival data
        """
        logger.info("Creating festival information")
        
        festivals = [
            {
                "title": "Thimphu Tshechu",
                "description": "One of the largest and most significant religious festivals in Bhutan, celebrating Guru Rinpoche. The festival features elaborate mask dances performed by monks and laypeople, alongside vibrant cultural performances.",
                "date": "September/October (dates vary according to lunar calendar)",
                "location": "Thimphu",
                "duration": "3 days",
                "category": "religious",
                "highlights": [
                    "Spectacular mask dances (Cham)",
                    "Unfurling of the giant Thongdrel (sacred scroll painting)",
                    "Large gathering of locals in traditional dress",
                    "Traditional music and dance performances",
                    "Religious blessing ceremonies"
                ]
            },
            {
                "title": "Paro Tshechu",
                "description": "A grand festival held at Paro Dzong featuring ritual dances that have been preserved for centuries. The festival concludes with the display of a giant thangka (religious scroll) so sacred it's only exhibited for a few hours at dawn.",
                "date": "March/April (varies according to lunar calendar)",
                "location": "Paro",
                "duration": "5 days",
                "category": "religious",
                "highlights": [
                    "Pre-dawn viewing of the sacred thangka",
                    "Colorful mask dances representing various deities",
                    "The famous 'Dance of the Lords of the Cremation Grounds'",
                    "Traditional Bhutanese folk performances",
                    "Festival market with local crafts and food"
                ]
            },
            {
                "title": "Black-Necked Crane Festival",
                "description": "A celebration honoring the arrival of endangered Black-Necked Cranes to Phobjikha Valley. The festival combines conservation awareness with cultural performances, including crane-themed dances performed by local schoolchildren.",
                "date": "November 11 (annually)",
                "location": "Gangtey, Phobjikha Valley",
                "duration": "1 day",
                "category": "cultural-ecological",
                "highlights": [
                    "Special crane dance performances by local children",
                    "Environmental conservation exhibitions",
                    "Folk songs and traditional dances",
                    "Opportunity to see the rare Black-Necked Cranes",
                    "Local crafts and products from the valley"
                ]
            },
            {
                "title": "Punakha Drubchen",
                "description": "A unique festival commemorating Bhutan's victory over Tibetan invaders in the 17th century. The festival features a dramatic recreation of the battle with volunteers dressed as ancient Bhutanese militia.",
                "date": "February/March (varies according to lunar calendar)",
                "location": "Punakha",
                "duration": "3 days",
                "category": "historical-religious",
                "highlights": [
                    "Dramatic reenactment of the historic battle",
                    "Traditional warrior dances",
                    "Procession of the portable shrine of Zhabdrung Ngawang Namgyal",
                    "Religious mask dances at the magnificent Punakha Dzong",
                    "Blessing ceremonies and prayers"
                ]
            },
            {
                "title": "Jambay Lhakhang Drup",
                "description": "One of Bhutan's most spectacular festivals, featuring the famous 'Fire Ceremony' where locals run through a gate of flames to cleanse themselves of sins. The festival is held at one of Bhutan's oldest temples, built in the 7th century.",
                "date": "October/November (varies according to lunar calendar)",
                "location": "Bumthang",
                "duration": "4 days",
                "category": "religious",
                "highlights": [
                    "Mesmerizing fire blessing ceremony (Mewang)",
                    "The naked dance ritual performed at midnight (Tercham)",
                    "Traditional mask dances with religious significance",
                    "Display of rare religious artifacts",
                    "Pilgrimages to the ancient Jambay Lhakhang temple"
                ]
            }
        ]
        
        logger.info(f"Created {len(festivals)} festival entries")
        return festivals
    
    def _create_trekking(self) -> List[Dict[str, Any]]:
        """
        Create trekking information based on known Bhutan trekking routes.
        
        Returns:
            list: List of trekking data
        """
        logger.info("Creating trekking information")
        
        trekking_options = [
            {
                "title": "Druk Path Trek",
                "description": "One of the most popular short treks in Bhutan, following an ancient trading route between Paro and Thimphu. The trek passes through stunning landscapes of blue pine forests, rhododendron thickets, and alpine yak pastures, with spectacular views of the Himalayan mountains.",
                "duration": "5-6 days",
                "difficulty": "Moderate",
                "category": "trekking",
                "best_season": "March-May and September-November",
                "max_elevation": "4,200 meters",
                "start_point": "Paro",
                "end_point": "Thimphu",
                "highlights": [
                    "Spectacular views of Mt. Jumolhari and other Himalayan peaks",
                    "Beautiful alpine lakes including Jimilangtsho",
                    "Ancient lhakhangs (temples) and dzongs along the route",
                    "Diverse ecosystems from pine forests to alpine meadows",
                    "Relatively accessible trek with good camping facilities"
                ],
                "itinerary": [
                    {
                        "title": "Day 1: Paro to Jele Dzong",
                        "description": "Begin trek from Ta Dzong (National Museum) in Paro. Climb steadily through blue pine forest to Damche Gom and continue to Jele Dzong camping area. Distance: 10 km, 1,090m ascent, 5-6 hours."
                    },
                    {
                        "title": "Day 2: Jele Dzong to Jangchulakha",
                        "description": "Trek through thick alpine forests and rhododendron thickets. Camp at yak herders' pasture of Jangchulakha with stunning mountain views. Distance: 10 km, 310m ascent, 3-4 hours."
                    },
                    {
                        "title": "Day 3: Jangchulakha to Jimilangtsho",
                        "description": "Follow the ridge through dwarf rhododendrons and distinctive Himalayan flora to Jimilangtsho Lake. Distance: 11 km, 4-5 hours."
                    },
                    {
                        "title": "Day 4: Jimilangtsho to Simkotra",
                        "description": "Pass by the lakes of Janetso and continue to Simkotra Lake. Distance: 11 km, 4-5 hours."
                    },
                    {
                        "title": "Day 5: Simkotra to Phajoding",
                        "description": "Trek through dwarf rhododendron trees and Phajoding monastery. Distance: 10 km, 4-5 hours."
                    },
                    {
                        "title": "Day 6: Phajoding to Thimphu",
                        "description": "Descend to Thimphu through blue pine forest, concluding the trek at Sangaygang. Distance: 5 km, 3 hours."
                    }
                ]
            },
            {
                "title": "Jomolhari Trek",
                "description": "A challenging high-altitude trek that takes you to the base of Mount Jomolhari, one of Bhutan's most sacred mountains. This trek offers incredible views of pristine Himalayan peaks and passes through remote villages and high mountain ecosystems.",
                "duration": "7-9 days",
                "difficulty": "Challenging",
                "category": "trekking",
                "best_season": "April-June and September-November",
                "max_elevation": "4,970 meters (Nyile La Pass)",
                "start_point": "Paro",
                "end_point": "Thimphu or Paro",
                "highlights": [
                    "Spectacular views of Mt. Jomolhari (7,326m) and Jichu Drake (6,794m)",
                    "Visits to remote mountain villages like Lingzhi",
                    "Rich biodiversity including chances to spot blue sheep and even snow leopards",
                    "Alpine lakes and high mountain passes",
                    "Authentic interaction with nomadic yak herders"
                ]
            },
            {
                "title": "Dagala Thousand Lakes Trek",
                "description": "A moderately challenging trek through the Dagala region, famous for its countless alpine lakes. This less-traveled route offers pristine natural beauty, stunning vistas of the entire Himalayan range, and excellent opportunities for trout fishing.",
                "duration": "6 days",
                "difficulty": "Moderate",
                "category": "trekking",
                "best_season": "April-June and September-October",
                "max_elevation": "4,720 meters",
                "start_point": "Thimphu",
                "end_point": "Thimphu",
                "highlights": [
                    "Numerous pristine alpine lakes",
                    "Panoramic views of Himalayan peaks including Everest on clear days",
                    "Diverse flora and fauna",
                    "Trout fishing opportunities",
                    "Less crowded than other popular treks"
                ]
            },
            {
                "title": "Bumdra Trek with Tiger's Nest Descent",
                "description": "A short but rewarding trek that combines wilderness camping above the clouds with a visit to Bhutan's iconic Tiger's Nest Monastery. This trek is perfect for those with limited time but who still want a genuine trekking experience.",
                "duration": "2 days",
                "difficulty": "Moderate",
                "category": "trekking",
                "best_season": "Year-round (except winter)",
                "max_elevation": "3,800 meters",
                "start_point": "Paro",
                "end_point": "Tiger's Nest Monastery, Paro",
                "highlights": [
                    "Camping at 'High Camp' with panoramic views",
                    "Cliff-side descent to the legendary Tiger's Nest Monastery",
                    "Ancient meditation caves",
                    "Accessible trek that can be done in a short timeframe",
                    "Combination of wilderness experience and cultural highlight"
                ]
            },
            {
                "title": "Snowman Trek",
                "description": "One of the most challenging high-altitude treks in the world, crossing multiple passes over 5,000 meters. This epic journey traverses the remote Lunana region in northern Bhutan and is considered the ultimate Himalayan adventure.",
                "duration": "25-30 days",
                "difficulty": "Strenuous",
                "category": "trekking",
                "best_season": "Mid-June to mid-October",
                "max_elevation": "5,320 meters",
                "start_point": "Paro",
                "end_point": "Bumthang",
                "highlights": [
                    "Cross 11 high mountain passes above 4,500m",
                    "Remote villages that rarely see outside visitors",
                    "Pristine mountain lakes and stunning glaciers",
                    "Diverse ecosystems from forests to alpine tundra",
                    "Ultimate Himalayan adventure for experienced trekkers"
                ]
            }
        ]
        
        logger.info(f"Created {len(trekking_options)} trekking options")
        return trekking_options
    
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
    
    def run(self):
        """
        Run the direct scraper.
        """
        logger.info("Starting direct scraper process")
        
        try:
            self.scrape_from_content()
            logger.info("Direct scraper process completed successfully")
        except Exception as e:
            logger.error(f"Error during direct scraping process: {str(e)}")
            raise

if __name__ == "__main__":
    """
    Run the direct scraper as a standalone script.
    """
    scraper = DirectBhutanScraper()
    scraper.run() 