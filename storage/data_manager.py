"""
Data manager for storing and retrieving scraped data for the Tashi bot.
"""
import os
import json
from typing import Dict, List, Any, Optional, Union

import config
from utils.logger import get_logger

logger = get_logger("data_manager")

class DataManager:
    """
    Manages data storage and retrieval for the Tashi bot.
    """
    
    def __init__(self):
        """
        Initialize the data manager.
        """
        # Ensure data directory exists
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        # Data cache to avoid reading from disk repeatedly
        self._cache = {
            'tours': None,
            'festivals': None,
            'trekking': None,
            'itineraries': None
        }
        
        logger.info("DataManager initialized")
    
    def load_data(self, data_type: str) -> List[Dict[str, Any]]:
        """
        Load data from file.
        
        Args:
            data_type (str): Type of data to load ('tours', 'festivals', 'trekking', 'itineraries')
            
        Returns:
            list: List of data items
        """
        # Check if data is cached
        if self._cache.get(data_type) is not None:
            logger.debug(f"Returning cached {data_type} data")
            return self._cache[data_type]
        
        # Map data type to file path
        file_path = self._get_file_path(data_type)
        if not file_path:
            logger.error(f"Invalid data type: {data_type}")
            return []
        
        # Load data from file
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                logger.info(f"Loaded {len(data)} {data_type} from {file_path}")
                
                # Cache the data
                self._cache[data_type] = data
                
                return data
            else:
                logger.warning(f"Data file does not exist: {file_path}")
                return []
        
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return []
    
    def save_data(self, data_type: str, data: List[Dict[str, Any]]) -> bool:
        """
        Save data to file.
        
        Args:
            data_type (str): Type of data to save ('tours', 'festivals', 'trekking', 'itineraries')
            data (list): List of data items
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Map data type to file path
        file_path = self._get_file_path(data_type)
        if not file_path:
            logger.error(f"Invalid data type: {data_type}")
            return False
        
        # Save data to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Saved {len(data)} {data_type} to {file_path}")
            
            # Update cache
            self._cache[data_type] = data
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {str(e)}")
            return False
    
    def get_by_id(self, data_type: str, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific item by ID.
        
        Args:
            data_type (str): Type of data to search ('tours', 'festivals', 'trekking', 'itineraries')
            item_id (str): ID of the item to retrieve
            
        Returns:
            dict or None: The item if found, None otherwise
        """
        data = self.load_data(data_type)
        
        for item in data:
            if item.get('id') == item_id:
                return item
        
        logger.warning(f"Item with ID {item_id} not found in {data_type}")
        return None
    
    def search(self, data_type: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for items matching a query.
        
        Args:
            data_type (str): Type of data to search ('tours', 'festivals', 'trekking', 'itineraries')
            query (str): Search query
            
        Returns:
            list: List of matching items
        """
        data = self.load_data(data_type)
        results = []
        
        # Convert query to lowercase for case-insensitive search
        query = query.lower()
        
        for item in data:
            # Search in title
            if query in item.get('title', '').lower():
                results.append(item)
                continue
            
            # Search in description
            if query in item.get('description', '').lower():
                results.append(item)
                continue
            
            # Search in highlights
            highlights = item.get('highlights', [])
            for highlight in highlights:
                if query in highlight.lower():
                    results.append(item)
                    break
        
        logger.info(f"Found {len(results)} {data_type} matching '{query}'")
        return results
    
    def filter_by_duration(self, data_type: str, min_days: int = 0, max_days: int = None) -> List[Dict[str, Any]]:
        """
        Filter items by duration.
        
        Args:
            data_type (str): Type of data to filter ('tours', 'festivals', 'trekking', 'itineraries')
            min_days (int): Minimum number of days
            max_days (int): Maximum number of days (None for no upper limit)
            
        Returns:
            list: List of filtered items
        """
        data = self.load_data(data_type)
        results = []
        
        for item in data:
            # Extract duration as number of days
            duration_str = item.get('duration', '')
            try:
                # Attempt to extract number of days from duration string (e.g., "7 days")
                days = int(''.join(filter(str.isdigit, duration_str)))
                
                # Apply filter
                if days >= min_days and (max_days is None or days <= max_days):
                    results.append(item)
            
            except (ValueError, TypeError):
                # If we can't extract days, skip this item
                logger.warning(f"Could not parse duration from: {duration_str}")
                continue
        
        logger.info(f"Found {len(results)} {data_type} with duration between {min_days} and {max_days or 'any'} days")
        return results
    
    def update_item(self, data_type: str, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a specific item.
        
        Args:
            data_type (str): Type of data to update ('tours', 'festivals', 'trekking', 'itineraries')
            item_id (str): ID of the item to update
            updates (dict): Updates to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        data = self.load_data(data_type)
        
        for i, item in enumerate(data):
            if item.get('id') == item_id:
                # Apply updates
                data[i].update(updates)
                
                # Save updated data
                if self.save_data(data_type, data):
                    logger.info(f"Updated item {item_id} in {data_type}")
                    return True
                else:
                    logger.error(f"Failed to save updates for item {item_id} in {data_type}")
                    return False
        
        logger.warning(f"Item with ID {item_id} not found in {data_type}")
        return False
    
    def clear_cache(self):
        """
        Clear the data cache.
        """
        self._cache = {
            'tours': None,
            'festivals': None,
            'trekking': None,
            'itineraries': None
        }
        logger.info("Data cache cleared")
    
    def _get_file_path(self, data_type: str) -> Optional[str]:
        """
        Get the file path for a data type.
        
        Args:
            data_type (str): Type of data ('tours', 'festivals', 'trekking', 'itineraries')
            
        Returns:
            str or None: File path if valid data type, None otherwise
        """
        if data_type == 'tours':
            return config.TOURS_FILE
        elif data_type == 'festivals':
            return config.FESTIVALS_FILE
        elif data_type == 'trekking':
            return config.TREKKING_FILE
        elif data_type == 'itineraries':
            return config.ITINERARIES_FILE
        else:
            return None
    
    def get_data(self, data_type: str) -> List[Dict[str, Any]]:
        """
        Get data for the specified type, handling special data formats.
        
        Args:
            data_type (str): Type of data to get ('tours', 'festivals', 'trekking', 'itineraries')
            
        Returns:
            list: List of data items
        """
        # For trekking data, special handling to extract 'treks' array from the JSON
        if data_type == 'trekking':
            # Check if data is cached
            if self._cache.get(data_type) is not None:
                logger.debug(f"Returning cached {data_type} data")
                return self._cache[data_type]
                
            try:
                file_path = self._get_file_path(data_type)
                if not file_path or not os.path.exists(file_path):
                    logger.warning(f"Data file not found for type: {data_type}")
                    return []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                # Trekking data is stored with 'treks' as the key for the array
                if 'treks' in raw_data:
                    treks_data = raw_data['treks']
                    self._cache[data_type] = treks_data
                    logger.debug(f"Loaded and cached {len(treks_data)} {data_type} items")
                    return treks_data
                else:
                    logger.warning(f"No 'treks' key found in {data_type} data")
                    return []
            except Exception as e:
                logger.error(f"Error loading {data_type} data: {str(e)}")
                return []
        
        # For other data types, use the standard load_data method
        return self.load_data(data_type) 