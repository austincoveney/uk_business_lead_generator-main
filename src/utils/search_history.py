"""Search History Management

Manages search history for location and business type suggestions.
Provides recent searches and popular locations functionality.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PySide6.QtCore import QSettings

class SearchHistoryManager:
    """Manages search history and provides suggestions"""
    
    def __init__(self, settings: QSettings):
        self.settings = settings
        self.max_history_items = 50
        self.max_suggestions = 10
    
    def add_search(self, location: str, business_type: str = "") -> None:
        """Add a search to history
        
        Args:
            location: Search location
            business_type: Business type searched for
        """
        if not location.strip():
            return
            
        # Get current history
        history = self.get_search_history()
        
        # Create new search entry
        search_entry = {
            "location": location.strip(),
            "business_type": business_type.strip() if business_type else "",
            "timestamp": datetime.now().isoformat(),
            "count": 1
        }
        
        # Check if this search already exists
        existing_index = -1
        for i, entry in enumerate(history):
            if (entry["location"].lower() == location.lower() and 
                entry["business_type"].lower() == business_type.lower()):
                existing_index = i
                break
        
        if existing_index >= 0:
            # Update existing entry
            history[existing_index]["count"] += 1
            history[existing_index]["timestamp"] = datetime.now().isoformat()
            # Move to front
            history.insert(0, history.pop(existing_index))
        else:
            # Add new entry at the beginning
            history.insert(0, search_entry)
        
        # Limit history size
        if len(history) > self.max_history_items:
            history = history[:self.max_history_items]
        
        # Save to settings
        self.settings.setValue("search_history", json.dumps(history))
    
    def get_search_history(self) -> List[Dict]:
        """Get complete search history
        
        Returns:
            List of search history entries
        """
        history_json = self.settings.value("search_history", "[]")
        try:
            return json.loads(history_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_location_suggestions(self, query: str = "") -> List[str]:
        """Get location suggestions based on history and query
        
        Args:
            query: Current user input
            
        Returns:
            List of location suggestions
        """
        history = self.get_search_history()
        suggestions = []
        
        # Get unique locations from history
        locations = []
        for entry in history:
            location = entry["location"]
            if location not in locations:
                locations.append(location)
        
        if not query:
            # Return recent locations
            return locations[:self.max_suggestions]
        
        query_lower = query.lower()
        
        # Filter locations that match query
        for location in locations:
            if query_lower in location.lower():
                suggestions.append(location)
        
        # Add popular UK locations if not enough suggestions
        popular_locations = self.get_popular_uk_locations()
        for location in popular_locations:
            if (query_lower in location.lower() and 
                location not in suggestions and 
                len(suggestions) < self.max_suggestions):
                suggestions.append(location)
        
        return suggestions[:self.max_suggestions]
    
    def get_business_type_suggestions(self, query: str = "") -> List[str]:
        """Get business type suggestions based on history
        
        Args:
            query: Current user input
            
        Returns:
            List of business type suggestions
        """
        history = self.get_search_history()
        suggestions = []
        
        # Get unique business types from history
        business_types = []
        for entry in history:
            business_type = entry["business_type"]
            if business_type and business_type not in business_types:
                business_types.append(business_type)
        
        if not query:
            return business_types[:self.max_suggestions]
        
        query_lower = query.lower()
        
        # Filter business types that match query
        for business_type in business_types:
            if query_lower in business_type.lower():
                suggestions.append(business_type)
        
        return suggestions[:self.max_suggestions]
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent complete searches
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of recent search entries
        """
        history = self.get_search_history()
        return history[:limit]
    
    def clear_history(self) -> None:
        """Clear all search history"""
        self.settings.setValue("search_history", "[]")
    
    def remove_search(self, location: str, business_type: str = "") -> None:
        """Remove a specific search from history
        
        Args:
            location: Location to remove
            business_type: Business type to remove
        """
        history = self.get_search_history()
        
        # Find and remove the entry
        for i, entry in enumerate(history):
            if (entry["location"].lower() == location.lower() and 
                entry["business_type"].lower() == business_type.lower()):
                history.pop(i)
                break
        
        # Save updated history
        self.settings.setValue("search_history", json.dumps(history))
    
    def get_popular_uk_locations(self) -> List[str]:
        """Get list of popular UK locations for suggestions
        
        Returns:
            List of popular UK cities and towns
        """
        return [
            "London", "Birmingham", "Manchester", "Liverpool", "Leeds", "Sheffield",
            "Bristol", "Glasgow", "Edinburgh", "Newcastle", "Cardiff", "Belfast",
            "Nottingham", "Leicester", "Coventry", "Bradford", "Stoke-on-Trent",
            "Wolverhampton", "Plymouth", "Southampton", "Reading", "Derby",
            "Luton", "Northampton", "Portsmouth", "Preston", "Milton Keynes",
            "Aberdeen", "Swansea", "Dundee", "York", "Norwich", "Oxford",
            "Cambridge", "Ipswich", "Exeter", "Gloucester", "Bath", "Chester",
            "Canterbury", "Winchester", "Salisbury", "Chichester", "Truro",
            "St Albans", "Lichfield", "Ripon", "Wells", "Ely", "Bangor",
            "St Davids", "Armagh", "Newry", "Lisburn", "Derry", "Craigavon"
        ]
    
    def get_search_statistics(self) -> Dict:
        """Get statistics about search history
        
        Returns:
            Dictionary with search statistics
        """
        history = self.get_search_history()
        
        if not history:
            return {
                "total_searches": 0,
                "unique_locations": 0,
                "unique_business_types": 0,
                "most_searched_location": None,
                "most_searched_business_type": None
            }
        
        # Count locations and business types
        location_counts = {}
        business_type_counts = {}
        
        for entry in history:
            location = entry["location"]
            business_type = entry["business_type"]
            count = entry.get("count", 1)
            
            location_counts[location] = location_counts.get(location, 0) + count
            if business_type:
                business_type_counts[business_type] = business_type_counts.get(business_type, 0) + count
        
        # Find most searched
        most_searched_location = max(location_counts.items(), key=lambda x: x[1])[0] if location_counts else None
        most_searched_business_type = max(business_type_counts.items(), key=lambda x: x[1])[0] if business_type_counts else None
        
        return {
            "total_searches": len(history),
            "unique_locations": len(location_counts),
            "unique_business_types": len(business_type_counts),
            "most_searched_location": most_searched_location,
            "most_searched_business_type": most_searched_business_type
        }