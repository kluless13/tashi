"""
Recommendation engine for matching user preferences with travel options.
"""
from typing import Dict, List, Any, Optional
import re
from datetime import datetime, timedelta

from storage.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger("recommendation_engine")

class RecommendationEngine:
    """
    Engine for matching user preferences with travel options.
    """
    
    def __init__(self):
        """
        Initialize the recommendation engine.
        """
        self.data_manager = DataManager()
        logger.info("RecommendationEngine initialized")
    
    def recommend_by_preferences(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recommend travel options based on user preferences.
        
        Args:
            preferences (dict): User preferences
                - trip_type (str): Type of trip ('cultural', 'festival', 'trekking', 'custom')
                - duration (int): Preferred duration in days
                - travel_month (str): Preferred month of travel
                - interests (list): List of specific interests
                
        Returns:
            list: List of recommended travel options
        """
        logger.info(f"Generating recommendations based on preferences: {preferences}")
        
        # Determine data type based on trip type
        trip_type = preferences.get('trip_type', '').lower()
        if trip_type == 'cultural':
            data_type = 'tours'
        elif trip_type == 'festival':
            data_type = 'festivals'
        elif trip_type == 'trekking':
            data_type = 'trekking'
        else:
            # For custom trips, check all data types
            return self._recommend_custom(preferences)
        
        # Get base data
        data = self.data_manager.load_data(data_type)
        
        # Filter by duration if specified
        duration = preferences.get('duration')
        if duration:
            try:
                duration_days = int(duration)
                # Allow for some flexibility in duration (±2 days)
                min_days = max(1, duration_days - 2)
                max_days = duration_days + 2
                data = self.data_manager.filter_by_duration(data_type, min_days, max_days)
            except (ValueError, TypeError):
                logger.warning(f"Invalid duration value: {duration}")
        
        # Filter by travel month if specified
        travel_month = preferences.get('travel_month')
        if travel_month:
            data = self._filter_by_travel_month(data, travel_month)
        
        # Filter by interests if specified
        interests = preferences.get('interests', [])
        if interests:
            data = self._filter_by_interests(data, interests)
        
        # Sort results by relevance (simple implementation)
        results = self._sort_by_relevance(data, preferences)
        
        logger.info(f"Generated {len(results)} recommendations")
        return results
    
    def _recommend_custom(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate custom recommendations across all data types.
        
        Args:
            preferences (dict): User preferences
            
        Returns:
            list: List of recommended travel options
        """
        all_results = []
        
        # Check each data type
        for data_type in ['tours', 'festivals', 'trekking', 'itineraries']:
            # Get base data
            data = self.data_manager.load_data(data_type)
            
            # Filter by duration if specified
            duration = preferences.get('duration')
            if duration:
                try:
                    duration_days = int(duration)
                    # Allow for some flexibility in duration (±2 days)
                    min_days = max(1, duration_days - 2)
                    max_days = duration_days + 2
                    data = self.data_manager.filter_by_duration(data_type, min_days, max_days)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid duration value: {duration}")
            
            # Filter by travel month if specified
            travel_month = preferences.get('travel_month')
            if travel_month:
                data = self._filter_by_travel_month(data, travel_month)
            
            # Filter by interests if specified
            interests = preferences.get('interests', [])
            if interests:
                data = self._filter_by_interests(data, interests)
            
            # Add data type as source
            for item in data:
                item['source'] = data_type
            
            all_results.extend(data)
        
        # Sort all results by relevance
        sorted_results = self._sort_by_relevance(all_results, preferences)
        
        # Limit to top 10 recommendations
        top_results = sorted_results[:10]
        
        logger.info(f"Generated {len(top_results)} custom recommendations")
        return top_results
    
    def _filter_by_travel_month(self, data: List[Dict[str, Any]], travel_month: str) -> List[Dict[str, Any]]:
        """
        Filter data by preferred travel month.
        
        Args:
            data (list): List of travel options
            travel_month (str): Preferred month of travel
            
        Returns:
            list: Filtered list of travel options
        """
        filtered_data = []
        
        # Try to parse the month
        try:
            # Convert month name to month number
            target_month = datetime.strptime(travel_month, "%B").month
        except ValueError:
            try:
                # Try short month name
                target_month = datetime.strptime(travel_month, "%b").month
            except ValueError:
                try:
                    # Try month number
                    target_month = int(travel_month)
                    if target_month < 1 or target_month > 12:
                        raise ValueError("Month number out of range")
                except ValueError:
                    logger.warning(f"Invalid month format: {travel_month}")
                    return data  # Return original data if month is invalid
        
        # Filter based on best season or available dates
        for item in data:
            # Check if item has season information
            season = item.get('best_season', '').lower()
            
            # Map seasons to months (approximate)
            if season:
                if target_month in [12, 1, 2] and any(s in season for s in ['winter', 'december', 'january', 'february']):
                    filtered_data.append(item)
                elif target_month in [3, 4, 5] and any(s in season for s in ['spring', 'march', 'april', 'may']):
                    filtered_data.append(item)
                elif target_month in [6, 7, 8] and any(s in season for s in ['summer', 'june', 'july', 'august']):
                    filtered_data.append(item)
                elif target_month in [9, 10, 11] and any(s in season for s in ['fall', 'autumn', 'september', 'october', 'november']):
                    filtered_data.append(item)
                elif 'year-round' in season or 'all year' in season:
                    filtered_data.append(item)
            else:
                # If no season information, check if item has specific dates
                dates = item.get('dates', [])
                if dates:
                    for date_range in dates:
                        if isinstance(date_range, dict):
                            start_date = date_range.get('start')
                            end_date = date_range.get('end')
                            
                            if start_date and end_date:
                                try:
                                    start = datetime.strptime(start_date, "%Y-%m-%d")
                                    end = datetime.strptime(end_date, "%Y-%m-%d")
                                    
                                    # Check if the target month falls within this date range
                                    if (start.month <= target_month <= end.month) or \
                                       (end.month < start.month and (target_month >= start.month or target_month <= end.month)):
                                        filtered_data.append(item)
                                        break
                                except ValueError:
                                    # If date parsing fails, skip this date range
                                    continue
                else:
                    # If no season or dates information, include the item anyway
                    filtered_data.append(item)
        
        logger.info(f"Filtered {len(data)} items to {len(filtered_data)} based on travel month {travel_month}")
        return filtered_data if filtered_data else data  # Return original data if no matches
    
    def _filter_by_interests(self, data: List[Dict[str, Any]], interests: List[str]) -> List[Dict[str, Any]]:
        """
        Filter data by user interests.
        
        Args:
            data (list): List of travel options
            interests (list): List of user interests
            
        Returns:
            list: Filtered list of travel options
        """
        if not interests:
            return data
        
        # Convert interests to lowercase for case-insensitive matching
        interests_lower = [interest.lower() for interest in interests]
        
        matching_items = []
        
        for item in data:
            item_score = 0
            
            # Check title
            title = item.get('title', '').lower()
            for interest in interests_lower:
                if interest in title:
                    item_score += 3  # Higher weight for title matches
            
            # Check description
            description = item.get('description', '').lower()
            for interest in interests_lower:
                if interest in description:
                    item_score += 2  # Medium weight for description matches
            
            # Check highlights
            highlights = item.get('highlights', [])
            for highlight in highlights:
                highlight_lower = highlight.lower()
                for interest in interests_lower:
                    if interest in highlight_lower:
                        item_score += 1  # Lower weight for highlight matches
            
            # If the item has any matches, add it to the results with its score
            if item_score > 0:
                item['relevance_score'] = item_score
                matching_items.append(item)
        
        # Sort by relevance score (highest first)
        matching_items.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Filtered {len(data)} items to {len(matching_items)} based on interests {interests}")
        return matching_items if matching_items else data  # Return original data if no matches
    
    def _sort_by_relevance(self, data: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sort data by relevance to user preferences.
        
        Args:
            data (list): List of travel options
            preferences (dict): User preferences
            
        Returns:
            list: Sorted list of travel options
        """
        # Copy the data to avoid modifying the original
        sorted_data = data.copy()
        
        for item in sorted_data:
            relevance_score = item.get('relevance_score', 0)
            
            # Boost score for duration match
            if 'duration' in preferences and 'duration' in item:
                try:
                    pref_duration = int(preferences['duration'])
                    item_duration = int(''.join(filter(str.isdigit, item['duration'])))
                    
                    # Exact match gets highest boost
                    if item_duration == pref_duration:
                        relevance_score += 5
                    # Close match gets medium boost
                    elif abs(item_duration - pref_duration) <= 2:
                        relevance_score += 3
                    # Further match gets small boost
                    elif abs(item_duration - pref_duration) <= 4:
                        relevance_score += 1
                except (ValueError, TypeError):
                    pass
            
            # Update the relevance score
            item['relevance_score'] = relevance_score
        
        # Sort by relevance score (highest first)
        sorted_data.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return sorted_data
    
    def get_recommendation_details(self, recommendation_id: str, source: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific recommendation.
        
        Args:
            recommendation_id (str): ID of the recommendation
            source (str): Source data type ('tours', 'festivals', 'trekking', 'itineraries')
            
        Returns:
            dict or None: Detailed information if found, None otherwise
        """
        return self.data_manager.get_by_id(source, recommendation_id) 