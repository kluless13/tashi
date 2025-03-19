"""
Conversation flow management for the Tashi bot.
"""
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Union
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

import config
from utils.logger import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger("conversation")

# Initialize OpenAI client with the API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
    logger.info("OpenAI API key loaded")
else:
    logger.warning("OpenAI API key not found. Falling back to rule-based responses.")

class ConversationState(Enum):
    """
    Possible states in the conversation flow.
    """
    GREETING = auto()  # Initial greeting
    TRIP_TYPE = auto()  # Asking for trip type
    DURATION = auto()  # Asking for duration
    TRAVEL_DATE = auto()  # Asking for travel date/month
    INTERESTS = auto()  # Asking for specific interests
    RECOMMENDATIONS = auto()  # Showing recommendations
    RECOMMENDATION_DETAILS = auto()  # Showing details of a selected recommendation
    FINALIZATION = auto()  # Finalizing the plan
    COMPLETED = auto()  # Conversation completed

class ConversationManager:
    """
    Manages the conversation flow for the Tashi bot.
    """
    
    def __init__(self):
        """
        Initialize the conversation manager.
        """
        # Storage for active conversations
        self.conversations = {}
        
        # Template for system prompt to guide OpenAI model
        self.system_prompt = """
        You are Tashi, a helpful travel planning assistant for Breathe Bhutan, a boutique travel agency.
        Your goal is to help users plan their ideal trip to Bhutan by understanding their preferences
        and providing personalized recommendations.
        
        Be friendly, knowledgeable about Bhutan's culture, festivals, trekking routes, and tourist attractions.
        Provide concise but helpful responses. Use a conversational tone.
        
        Current conversation state: {state}
        User preferences so far: {preferences}
        """
        
        logger.info("ConversationManager initialized")
    
    def start_conversation(self, user_id: int) -> str:
        """
        Start a new conversation with a user.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            str: Initial message to send to the user
        """
        # Initialize conversation state and data
        self.conversations[user_id] = {
            'state': ConversationState.GREETING,
            'preferences': {},
            'recommendations': [],
            'selected_recommendation': None,
            'message_history': []  # Store conversation history for context
        }
        
        logger.info(f"Started new conversation with user {user_id}")
        
        # Use OpenAI for welcome message if available
        if client:
            try:
                welcome_message = self._generate_ai_response(
                    user_id,
                    "I'd like to plan a trip to Bhutan.",
                    include_history=False
                )
                if welcome_message:
                    # Save this interaction to history
                    self._add_to_history(user_id, "I'd like to plan a trip to Bhutan.", welcome_message)
                    return welcome_message
            except Exception as e:
                logger.error(f"Error generating AI welcome message: {str(e)}")
        
        # Fallback to standard welcome message
        return config.WELCOME_MESSAGE
    
    def process_message(self, user_id: int, message_text: str) -> str:
        """
        Process a message from the user and advance the conversation.
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): Message text from the user
            
        Returns:
            str: Response message to send to the user
        """
        # Check if conversation exists, if not start a new one
        if user_id not in self.conversations:
            logger.warning(f"No active conversation found for user {user_id}, starting a new one")
            return self.start_conversation(user_id)
        
        # Get the current conversation state and data
        conversation = self.conversations[user_id]
        current_state = conversation['state']
        
        # Save user message to history
        self._add_to_history(user_id, message_text, None)
        
        # Try to use OpenAI for generating response if available
        if client:
            try:
                # Process the state transition based on message
                self._update_state_from_message(user_id, message_text, current_state)
                
                # Generate AI response
                ai_response = self._generate_ai_response(user_id, message_text)
                
                if ai_response:
                    # Save AI response to history
                    self._add_to_history(user_id, None, ai_response)
                    return ai_response
            except Exception as e:
                logger.error(f"Error with AI response generation: {str(e)}")
                # Continue with rule-based approach on failure
        
        # Fallback to rule-based approach
        return self._process_message_rule_based(user_id, message_text)
    
    def _process_message_rule_based(self, user_id: int, message_text: str) -> str:
        """
        Process message using rule-based approach (original implementation).
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): Message text from the user
            
        Returns:
            str: Response message
        """
        # Get the current conversation state and data
        conversation = self.conversations[user_id]
        current_state = conversation['state']
        
        # Process message based on current state
        if current_state == ConversationState.GREETING:
            # Transition to asking for trip type
            conversation['state'] = ConversationState.TRIP_TYPE
            # Create a keyboard with trip type options
            response = self._create_trip_type_keyboard()
        
        elif current_state == ConversationState.TRIP_TYPE:
            # Process trip type response
            trip_type = self._process_trip_type(message_text)
            conversation['preferences']['trip_type'] = trip_type
            
            # Transition to asking for duration and travel date together
            conversation['state'] = ConversationState.DURATION
            response = "Great choice! How many days are you planning to stay in Bhutan, and when are you planning to visit? (Example: '7 days in October')"
        
        elif current_state == ConversationState.DURATION:
            # Process combined duration and travel date response
            duration, travel_month = self._process_duration_and_date(message_text)
            conversation['preferences']['duration'] = duration
            conversation['preferences']['travel_month'] = travel_month
            
            # Transition to asking for interests
            conversation['state'] = ConversationState.INTERESTS
            response = "What specific interests do you have for your trip to Bhutan? (e.g., culture, nature, hiking, spirituality, photography)"
        
        elif current_state == ConversationState.TRAVEL_DATE:
            # This state is skipped now as we combine duration and travel date
            # But we keep it for backwards compatibility
            travel_month = self._process_travel_date(message_text)
            conversation['preferences']['travel_month'] = travel_month
            
            # Transition to asking for interests
            conversation['state'] = ConversationState.INTERESTS
            response = "What specific interests do you have for your trip to Bhutan? (e.g., culture, nature, hiking, spirituality, photography)"
        
        elif current_state == ConversationState.INTERESTS:
            # Process interests response
            interests = self._process_interests(message_text)
            conversation['preferences']['interests'] = interests
            
            # Transition to recommendations
            conversation['state'] = ConversationState.RECOMMENDATIONS
            
            # Get recommendations from the recommendation engine based on preferences
            from recommendation.engine import RecommendationEngine
            recommendation_engine = RecommendationEngine()
            recommendations = recommendation_engine.recommend_by_preferences(conversation['preferences'])
            
            # Update festival dates with current year if needed
            if conversation['preferences'].get('trip_type') == 'festival':
                recommendations = self._update_festival_dates(recommendations, conversation['preferences'].get('travel_month'))
                
            conversation['recommendations'] = recommendations
            
            # Format recommendations as a message with buttons
            response = self._format_recommendations_with_buttons(conversation['recommendations'])
        
        elif current_state == ConversationState.RECOMMENDATIONS:
            # Process selection of a recommendation
            selection = self._process_recommendation_selection(message_text, conversation['recommendations'])
            
            if selection:
                # User selected a recommendation
                conversation['selected_recommendation'] = selection
                conversation['state'] = ConversationState.RECOMMENDATION_DETAILS
                
                # Format the recommendation details with confirmation buttons
                response = self._format_recommendation_details_with_buttons(selection)
            else:
                # User didn't make a valid selection, ask again
                response = "Please select a recommendation by number (e.g., '1' for the first option), or say 'more' to see additional options."
        
        elif current_state == ConversationState.RECOMMENDATION_DETAILS:
            # Process response to recommendation details
            if self._is_affirmative(message_text):
                # User confirmed this recommendation
                conversation['state'] = ConversationState.FINALIZATION
                
                # In the actual implementation, this would send the details to the Breathe Bhutan team
                response = "Great! I'll finalize your travel plan. Could you please provide your name and email so the Breathe Bhutan team can contact you?"
            elif self._is_negative(message_text):
                # User rejected this recommendation, go back to recommendations
                conversation['state'] = ConversationState.RECOMMENDATIONS
                response = "No problem! Let's look at other options.\n\n" + self._format_recommendations_with_buttons(conversation['recommendations'])
            else:
                # User didn't give a clear yes/no
                response = self._format_confirmation_buttons("Would you like to proceed with this travel plan?")
        
        elif current_state == ConversationState.FINALIZATION:
            # Process contact information
            contact_info = self._process_contact_info(message_text)
            conversation['contact_info'] = contact_info
            
            # Transition to completed state
            conversation['state'] = ConversationState.COMPLETED
            
            # In the actual implementation, this would send the finalized plan and contact info to the Breathe Bhutan team
            response = config.FINALIZATION_MESSAGE
        
        elif current_state == ConversationState.COMPLETED:
            # Conversation is completed, start a new one if user wants to
            if self._is_restart(message_text):
                return self.start_conversation(user_id)
            else:
                response = "Your travel plan has been sent to the Breathe Bhutan team. If you'd like to plan another trip, just say 'start over'."
        
        else:
            # Default response for unhandled states
            logger.error(f"Unhandled conversation state: {current_state}")
            response = "I'm sorry, I didn't understand that. Could you please try again?"
        
        # Save response to history
        self._add_to_history(user_id, None, response)
        
        return response
    
    def _update_state_from_message(self, user_id: int, message_text: str, current_state: ConversationState) -> None:
        """
        Update the conversation state based on the message.
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): Message text from the user
            current_state (ConversationState): Current conversation state
        """
        conversation = self.conversations[user_id]
        
        # State transitions
        if current_state == ConversationState.GREETING:
            # Always move to trip type after greeting
            conversation['state'] = ConversationState.TRIP_TYPE
        
        elif current_state == ConversationState.TRIP_TYPE:
            # Extract trip type and move to duration
            trip_type = self._process_trip_type(message_text)
            conversation['preferences']['trip_type'] = trip_type
            conversation['state'] = ConversationState.DURATION
        
        elif current_state == ConversationState.DURATION:
            # Extract duration and date, then move to interests
            duration, travel_month = self._process_duration_and_date(message_text)
            conversation['preferences']['duration'] = duration
            conversation['preferences']['travel_month'] = travel_month
            conversation['state'] = ConversationState.INTERESTS
        
        elif current_state == ConversationState.TRAVEL_DATE:
            # Extract travel date and move to interests
            travel_month = self._process_travel_date(message_text)
            conversation['preferences']['travel_month'] = travel_month
            conversation['state'] = ConversationState.INTERESTS
        
        elif current_state == ConversationState.INTERESTS:
            # Extract interests and move to recommendations
            interests = self._process_interests(message_text)
            conversation['preferences']['interests'] = interests
            conversation['state'] = ConversationState.RECOMMENDATIONS
            
            # Get recommendations from the recommendation engine
            from recommendation.engine import RecommendationEngine
            recommendation_engine = RecommendationEngine()
            recommendations = recommendation_engine.recommend_by_preferences(conversation['preferences'])
            
            # Update festival dates with current year if needed
            if conversation['preferences'].get('trip_type') == 'festival':
                recommendations = self._update_festival_dates(recommendations, conversation['preferences'].get('travel_month'))
                
            conversation['recommendations'] = recommendations
        
        elif current_state == ConversationState.RECOMMENDATIONS:
            # Try to process selection
            selection = self._process_recommendation_selection(message_text, conversation['recommendations'])
            if selection:
                conversation['selected_recommendation'] = selection
                conversation['state'] = ConversationState.RECOMMENDATION_DETAILS
        
        elif current_state == ConversationState.RECOMMENDATION_DETAILS:
            # Check for yes/no response
            if self._is_affirmative(message_text):
                conversation['state'] = ConversationState.FINALIZATION
            elif self._is_negative(message_text):
                conversation['state'] = ConversationState.RECOMMENDATIONS
        
        elif current_state == ConversationState.FINALIZATION:
            # Process contact info and move to completed
            contact_info = self._process_contact_info(message_text)
            conversation['contact_info'] = contact_info
            conversation['state'] = ConversationState.COMPLETED
        
        elif current_state == ConversationState.COMPLETED:
            # Check for restart request
            if self._is_restart(message_text):
                # Reset conversation (will be handled in process_message)
                pass
    
    def _generate_ai_response(self, user_id: int, message_text: str, include_history: bool = True) -> str:
        """
        Generate a response using OpenAI's API.
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): Current message from the user
            include_history (bool): Whether to include conversation history
            
        Returns:
            str: Generated response
        """
        if not client:
            return None
        
        try:
            conversation = self.conversations[user_id]
            current_state = conversation['state']
            
            # Get current year for festival dates
            from datetime import datetime
            current_year = datetime.now().year
            
            # Prepare system prompt with current state and preferences
            system_prompt = self.system_prompt.format(
                state=current_state.name,
                preferences=json.dumps(conversation['preferences'], indent=2) if conversation['preferences'] else "None yet"
            )
            
            # Add guidance about using current year for festival dates
            if conversation['preferences'].get('trip_type') == 'festival':
                system_prompt += f"\n\nIMPORTANT: When discussing festivals, ALWAYS use {current_year} or {current_year + 1} as the year for upcoming festivals. NEVER use outdated years like 2022 or 2023. If a festival date is in the past for this year, refer to next year's date."
            
            # Build messages for OpenAI API
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if needed
            if include_history and len(conversation['message_history']) > 0:
                # Include up to last 5 exchanges (10 messages) for context
                history = conversation['message_history'][-10:]
                for entry in history:
                    if entry['user_message']:
                        messages.append({"role": "user", "content": entry['user_message']})
                    if entry['assistant_message']:
                        messages.append({"role": "assistant", "content": entry['assistant_message']})
            
            # Add current user message if not already in history
            if not include_history or conversation['message_history'][-1]['user_message'] != message_text:
                messages.append({"role": "user", "content": message_text})
            
            # Add guidance based on current state
            state_guidance = self._get_state_guidance(current_state, conversation)
            if state_guidance:
                messages.append({"role": "system", "content": state_guidance})
            
            # Call OpenAI API using the new client format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract and return the response content
            assistant_message = response.choices[0].message.content.strip()
            return assistant_message
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return None
    
    def _get_state_guidance(self, state: ConversationState, conversation: Dict) -> str:
        """
        Get state-specific guidance for the AI model.
        
        Args:
            state (ConversationState): Current state
            conversation (dict): Conversation data
            
        Returns:
            str: Guidance for the AI model
        """
        # Get current year for festival dates
        from datetime import datetime
        current_year = datetime.now().year
        
        if state == ConversationState.GREETING:
            return "The user is starting a conversation. Introduce yourself as Tashi, a travel assistant for Breathe Bhutan. Ask about what kind of trip they're interested in."
        
        elif state == ConversationState.TRIP_TYPE:
            return "Ask the user what type of trip they're interested in (cultural tours, festivals, trekking, or a custom itinerary). Explain briefly what each option means."
        
        elif state == ConversationState.DURATION:
            return f"The user is interested in {conversation['preferences'].get('trip_type', 'a trip')} to Bhutan. Ask how many days they plan to stay."
        
        elif state == ConversationState.TRAVEL_DATE:
            return f"The user is planning a {conversation['preferences'].get('duration', '')} day trip. Ask about their preferred travel dates or month."
        
        elif state == ConversationState.INTERESTS:
            return f"The user wants to travel in {conversation['preferences'].get('travel_month', '')}. Ask about their specific interests in Bhutan (culture, spirituality, nature, photography, etc.)."
        
        elif state == ConversationState.RECOMMENDATIONS:
            recommendations = conversation.get('recommendations', [])
            guidance = f"Based on preferences, offer these {len(recommendations)} recommendations. Ask which one sounds most appealing."
            
            # Add festival-specific guidance if needed
            if conversation['preferences'].get('trip_type') == 'festival':
                guidance += f"\n\nIMPORTANT: For all festival dates, use only {current_year} or {current_year + 1} as the year. If a festival's date has already passed this year, refer to next year's festival ({current_year + 1})."
            
            return guidance
        
        elif state == ConversationState.RECOMMENDATION_DETAILS:
            selected = conversation.get('selected_recommendation', {})
            
            # Get name from selected recommendation (respecting different data structures)
            title = selected.get('title', selected.get('name', 'this option'))
            
            guidance = f"The user is interested in '{title}'. Provide more details and ask if they want to proceed with this plan."
            
            # Add festival-specific guidance if needed
            if conversation['preferences'].get('trip_type') == 'festival':
                guidance += f"\n\nIf referring to festival dates, ONLY use {current_year} or {current_year + 1} as the year (NOT 2022 or any other past year)."
            
            return guidance
        
        elif state == ConversationState.FINALIZATION:
            return "The user has confirmed their interest. Ask for their name and email to finalize the booking."
        
        elif state == ConversationState.COMPLETED:
            return "The trip is booked. Thank the user and let them know that Breathe Bhutan will contact them soon. They can also start over if they want to plan another trip."
        
        return None
    
    def _add_to_history(self, user_id: int, user_message: Optional[str], assistant_message: Optional[str]) -> None:
        """
        Add an exchange to the conversation history.
        
        Args:
            user_id (int): Telegram user ID
            user_message (str): Message from the user
            assistant_message (str): Message from the assistant
        """
        self.conversations[user_id]['message_history'].append({
            'user_message': user_message,
            'assistant_message': assistant_message
        })
        
        # Limit history size to prevent token overflow
        if len(self.conversations[user_id]['message_history']) > 20:
            self.conversations[user_id]['message_history'] = self.conversations[user_id]['message_history'][-20:]
    
    def _process_trip_type(self, message_text: str) -> str:
        """
        Process the user's trip type selection.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            str: Processed trip type
        """
        message_lower = message_text.lower()
        
        if 'cultural' in message_lower or 'culture' in message_lower:
            return 'cultural'
        elif 'festival' in message_lower:
            return 'festival'
        elif 'trek' in message_lower or 'hiking' in message_lower or 'adventure' in message_lower:
            return 'trekking'
        else:
            # Default to custom if no clear category is detected
            return 'custom'
    
    def _process_duration(self, message_text: str) -> int:
        """
        Process the user's duration response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            int: Number of days
        """
        # Extract numbers from the message
        import re
        numbers = re.findall(r'\d+', message_text)
        
        if numbers:
            # Return the first number found
            return int(numbers[0])
        else:
            # Default to 7 days if no number is found
            return 7
    
    def _process_travel_date(self, message_text: str) -> str:
        """
        Process the user's travel date/month response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            str: Processed travel month
        """
        message_lower = message_text.lower()
        
        # List of month names
        months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        # Check if any month name is in the message
        for i, month in enumerate(months):
            if month in message_lower:
                return month.capitalize()
            # Check for abbreviated month names (e.g., Jan, Feb)
            elif month[:3] in message_lower:
                return month.capitalize()
        
        # If no month name is found, check for seasons
        if any(season in message_lower for season in ['spring', 'april', 'may']):
            return 'April'  # Middle of spring
        elif any(season in message_lower for season in ['summer', 'july', 'august']):
            return 'July'  # Middle of summer
        elif any(season in message_lower for season in ['fall', 'autumn', 'october', 'november']):
            return 'October'  # Middle of fall
        elif any(season in message_lower for season in ['winter', 'january', 'february']):
            return 'January'  # Middle of winter
        
        # Default to current month+3 if no month or season is found
        from datetime import datetime
        current_month = datetime.now().month
        target_month = (current_month + 3) % 12
        if target_month == 0:
            target_month = 12
        return months[target_month - 1].capitalize()
    
    def _process_interests(self, message_text: str) -> List[str]:
        """
        Process the user's interests response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            list: List of interests
        """
        # Define common interests
        common_interests = [
            'culture', 'history', 'nature', 'hiking', 'trekking', 'mountains',
            'spirituality', 'buddhism', 'temples', 'dzongs', 'festivals',
            'photography', 'food', 'local', 'adventure', 'relaxation'
        ]
        
        message_lower = message_text.lower()
        interests = []
        
        # Check for each common interest in the message
        for interest in common_interests:
            if interest in message_lower:
                interests.append(interest)
        
        # If no interests were identified, extract nouns as potential interests
        if not interests:
            # Simple extraction based on common words
            words = message_lower.split()
            for word in words:
                # Exclude very short words and common stop words
                if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'have', 'would', 'about', 'like']:
                    interests.append(word)
        
        return interests if interests else ['culture', 'nature']  # Default interests if none found
    
    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Format recommendations as a message.
        
        Args:
            recommendations (list): List of recommendation items
            
        Returns:
            str: Formatted message
        """
        if not recommendations:
            return "I couldn't find any recommendations matching your preferences. Let's try again with different preferences."
        
        message = "Based on your preferences, here are some recommendations for your trip to Bhutan:\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            message += f"{i}. {rec['title']} ({rec['duration']})\n"
            message += f"   {rec['summary']}\n\n"
        
        message += "Which option interests you the most? Please respond with the number (e.g., '1' for the first option)."
        
        return message
    
    def _process_recommendation_selection(self, message_text: str, recommendations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Process the user's selection of a recommendation.
        
        Args:
            message_text (str): Message text from the user
            recommendations (list): List of available recommendations
            
        Returns:
            dict or None: Selected recommendation if valid, None otherwise
        """
        # Try to extract a number from the message
        import re
        numbers = re.findall(r'\d+', message_text)
        
        if numbers:
            selection = int(numbers[0])
            
            # Check if selection is valid
            if 1 <= selection <= len(recommendations):
                return recommendations[selection - 1]
        
        return None
    
    def _format_recommendation_details(self, recommendation: Dict[str, Any]) -> str:
        """
        Format the details of a recommendation.
        
        Args:
            recommendation (dict): Recommendation data
            
        Returns:
            str: Formatted recommendation details
        """
        # Handle different data structures (trekking vs other recommendations)
        title = recommendation.get('title', recommendation.get('name', 'Unknown'))
        duration = recommendation.get('duration', recommendation.get('duration_days', 'Unknown'))
        description = recommendation.get('description', recommendation.get('summary', ''))
        
        message = f"*{title}*\n\n"
        message += f"*Duration:* {duration} days\n\n"
        message += f"*Description:* {description}\n\n"
        
        # Add highlights if available
        highlights = recommendation.get('highlights', [])
        if highlights:
            message += "*Highlights:*\n"
            for highlight in highlights:
                message += f"- {highlight}\n"
            message += "\n"
        
        # Add difficulty level if available (for treks)
        difficulty = recommendation.get('difficulty_level')
        if difficulty:
            message += f"*Difficulty:* {difficulty}\n\n"
        
        # Add best season if available (for treks)
        best_season = recommendation.get('best_season')
        if best_season:
            if isinstance(best_season, list):
                best_season = ", ".join(best_season)
            message += f"*Best Season:* {best_season}\n\n"
        
        # Add daily itinerary if available
        itinerary = recommendation.get('daily_itinerary', [])
        if itinerary:
            message += "*Daily Itinerary:*\n"
            for day in itinerary[:3]:  # Show only first 3 days to avoid message too long
                message += f"Day {day.get('day')}: {day.get('title')} - {day.get('description')[:100]}...\n"
            if len(itinerary) > 3:
                message += "...(and more)\n"
            message += "\n"
        
        # Add itinerary summary if available (for treks without detailed itinerary)
        itinerary_summary = recommendation.get('daily_itinerary_summary')
        if itinerary_summary and not itinerary:
            message += f"*Itinerary Summary:* {itinerary_summary}\n\n"
        
        # Add images if available
        image_url = recommendation.get('image_url')
        if image_url:
            message += f"[View Image]({image_url})\n\n"
        
        # Add booking options
        message += "Would you like to book this trip or see other options?"
        
        return message
    
    def _process_contact_info(self, message_text: str) -> Dict[str, str]:
        """
        Process the user's contact information.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            dict: Extracted contact information
        """
        # Simple extraction of name and email
        import re
        
        # Extract email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, message_text)
        email = email_matches[0] if email_matches else ""
        
        # Extract name (everything before the email, or the whole message if no email)
        if email:
            name_part = message_text.split(email)[0].strip()
        else:
            name_part = message_text
        
        # Clean up the name (remove common phrases, greetings, etc.)
        common_phrases = ["my name is", "i am", "this is", "i'm", "name:", "email:"]
        for phrase in common_phrases:
            name_part = name_part.lower().replace(phrase, "").strip()
        
        # Capitalize the name
        name = " ".join(word.capitalize() for word in name_part.split())
        
        return {
            "name": name,
            "email": email
        }
    
    def _is_affirmative(self, message_text: str) -> bool:
        """
        Check if a message is an affirmative response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            bool: True if affirmative, False otherwise
        """
        affirmative_words = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'good', 'great', 'perfect']
        return any(word in message_text.lower() for word in affirmative_words)
    
    def _is_negative(self, message_text: str) -> bool:
        """
        Check if a message is a negative response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            bool: True if negative, False otherwise
        """
        negative_words = ['no', 'nope', 'not', "don't", 'dont', 'other', 'different', 'another', 'else']
        return any(word in message_text.lower() for word in negative_words)
    
    def _is_restart(self, message_text: str) -> bool:
        """
        Check if a message is a request to restart the conversation.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            bool: True if restart request, False otherwise
        """
        restart_words = ['start over', 'restart', 'reset', 'new', 'again', 'begin', 'another trip']
        return any(phrase in message_text.lower() for phrase in restart_words)
    
    def end_conversation(self, user_id: int) -> None:
        """
        End a conversation with a user.
        
        Args:
            user_id (int): Telegram user ID
        """
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Ended conversation with user {user_id}")
    
    def serialize_conversations(self) -> str:
        """
        Serialize all conversations to JSON.
        
        Returns:
            str: JSON string representation of conversations
        """
        # Convert enum values to strings for serialization
        serializable_convs = {}
        
        for user_id, conv in self.conversations.items():
            serializable_conv = dict(conv)
            serializable_conv['state'] = conv['state'].name
            
            # Don't include message history in serialization to keep it compact
            serializable_conv.pop('message_history', None)
            
            serializable_convs[user_id] = serializable_conv
        
        return json.dumps(serializable_convs)
    
    def deserialize_conversations(self, json_data: str) -> None:
        """
        Deserialize conversations from JSON.
        
        Args:
            json_data (str): JSON string representation of conversations
        """
        try:
            serialized_convs = json.loads(json_data)
            
            for user_id, conv in serialized_convs.items():
                # Convert string state back to enum
                conv['state'] = ConversationState[conv['state']]
                
                # Initialize empty message history
                conv['message_history'] = []
                
                self.conversations[int(user_id)] = conv
            
            logger.info(f"Deserialized {len(serialized_convs)} conversations")
        
        except Exception as e:
            logger.error(f"Error deserializing conversations: {str(e)}")
            # Initialize empty conversations if deserialization fails
            self.conversations = {}
    
    def _create_trip_type_keyboard(self) -> str:
        """
        Create a response with inline keyboard for trip type selection.
        
        Returns:
            str: Response with JSON-formatted inline keyboard
        """
        message = "What kind of experience are you looking for in Bhutan?"
        
        # Create keyboard buttons in JSON format for Telegram
        keyboard = {
            "inline_keyboard": [
                [{"text": "Cultural Tours", "callback_data": "cultural"}],
                [{"text": "Festivals", "callback_data": "festival"}],
                [{"text": "Trekking & Adventure", "callback_data": "trekking"}],
                [{"text": "Custom Itinerary", "callback_data": "custom"}]
            ]
        }
        
        # Convert keyboard to JSON string and attach to the message
        import json
        message += "\n\nPlease select one of the options below:"
        message += f"\n<<keyboard:{json.dumps(keyboard)}>>"  # This will be processed in the bot.py to create a real keyboard
        
        return message
    
    def _format_recommendations_with_buttons(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Format recommendations as a message with inline keyboard buttons.
        
        Args:
            recommendations (list): List of recommendation items
            
        Returns:
            str: Formatted message with keyboard
        """
        if not recommendations:
            return "I couldn't find any recommendations matching your preferences. Let's try again with different preferences."
        
        # Check if these are trekking recommendations
        is_trekking = any(rec.get('id', '').startswith('trek') or 'trek' in rec.get('id', '').lower() for rec in recommendations)
        
        # If these are trekking recommendations, load all available treks
        if is_trekking:
            try:
                # Load all treks from the data file
                import json
                import os
                
                treks_file = os.path.join('data', 'trekking', 'trekking.json')
                if os.path.exists(treks_file):
                    with open(treks_file, 'r', encoding='utf-8') as f:
                        all_treks_data = json.load(f)
                        all_treks = all_treks_data.get('treks', [])
                        
                    # Use all treks instead of the limited recommendations
                    if all_treks:
                        recommendations = all_treks
                        logger.info(f"Using all {len(all_treks)} treks from data file")
            except Exception as e:
                logger.error(f"Error loading all trek options: {str(e)}")
        
        message = "Based on your preferences, here are some recommendations for your trip to Bhutan:\n\n"
        
        # Display only a summary of the recommendations in the text message
        for i, rec in enumerate(recommendations[:5], 1):
            title = rec.get('title', rec.get('name', 'Unknown Trek'))
            duration = rec.get('duration', rec.get('duration_days', 'Unknown duration'))
            summary = rec.get('summary', rec.get('description', ''))
            # Truncate the summary if it's too long
            if len(summary) > 100:
                summary = summary[:97] + "..."
                
            message += f"{i}. {title} ({duration} days)\n"
            message += f"   {summary}\n\n"
        
        if len(recommendations) > 5:
            message += f"And {len(recommendations) - 5} more options available as buttons below.\n\n"
        
        # Create keyboard buttons in JSON format
        keyboard = {"inline_keyboard": []}
        
        # Create buttons in rows of 2 for better layout
        buttons = []
        for i, rec in enumerate(recommendations, 1):
            title = rec.get('title', rec.get('name', 'Unknown Trek'))
            button_text = f"{i}. {title}"
            
            # Truncate button text if too long
            if len(button_text) > 30:
                button_text = button_text[:27] + "..."
                
            buttons.append({
                "text": button_text,
                "callback_data": str(i)
            })
        
        # Arrange buttons in rows of 2
        for i in range(0, len(buttons), 2):
            row = [buttons[i]]
            if i + 1 < len(buttons):
                row.append(buttons[i + 1])
            keyboard["inline_keyboard"].append(row)
        
        # Add "start over" button in its own row
        keyboard["inline_keyboard"].append([{
            "text": "Start Over",
            "callback_data": "start over"
        }])
        
        # Convert keyboard to JSON string and attach to the message
        import json
        message += "Which option interests you the most? Please select one:"
        message += f"\n<<keyboard:{json.dumps(keyboard)}>>"
        
        return message
    
    def _format_recommendation_details_with_buttons(self, recommendation: Dict[str, Any]) -> str:
        """
        Format recommendation details as a message with inline keyboard buttons.
        
        Args:
            recommendation (dict): Recommendation data
            
        Returns:
            str: Formatted message with keyboard
        """
        # Handle different data structures (trekking vs other recommendations)
        title = recommendation.get('title', recommendation.get('name', 'Unknown'))
        duration = recommendation.get('duration', recommendation.get('duration_days', 'Unknown'))
        description = recommendation.get('description', recommendation.get('summary', ''))
        
        message = f"*{title}*\n\n"
        message += f"*Duration:* {duration} days\n\n"
        message += f"*Description:* {description}\n\n"
        
        # Add highlights if available
        highlights = recommendation.get('highlights', [])
        if highlights:
            message += "*Highlights:*\n"
            for highlight in highlights:
                message += f"- {highlight}\n"
            message += "\n"
        
        # Add difficulty level if available (for treks)
        difficulty = recommendation.get('difficulty_level')
        if difficulty:
            message += f"*Difficulty:* {difficulty}\n\n"
        
        # Add best season if available (for treks)
        best_season = recommendation.get('best_season')
        if best_season:
            if isinstance(best_season, list):
                best_season = ", ".join(best_season)
            message += f"*Best Season:* {best_season}\n\n"
        
        # Add daily itinerary if available
        itinerary = recommendation.get('daily_itinerary', [])
        if itinerary:
            message += "*Daily Itinerary:*\n"
            for day in itinerary[:3]:  # Show only first 3 days to avoid message too long
                message += f"Day {day.get('day')}: {day.get('title')} - {day.get('description')[:100]}...\n"
            if len(itinerary) > 3:
                message += "...(and more)\n"
            message += "\n"
        
        # Add itinerary summary if available (for treks without detailed itinerary)
        itinerary_summary = recommendation.get('daily_itinerary_summary')
        if itinerary_summary and not itinerary:
            message += f"*Itinerary Summary:* {itinerary_summary}\n\n"
        
        # Add images if available
        image_url = recommendation.get('image_url')
        if image_url:
            message += f"[View Image]({image_url})\n\n"
        
        # Create keyboard buttons in JSON format
        keyboard = {"inline_keyboard": [
            [
                {"text": "Book This Trip", "callback_data": "book"},
                {"text": "See Other Options", "callback_data": "back"}
            ],
            [
                {"text": "Start Over", "callback_data": "start over"}
            ]
        ]}
        
        # Convert keyboard to JSON string and attach to the message
        import json
        message += "What would you like to do next?"
        message += f"\n<<keyboard:{json.dumps(keyboard)}>>"
        
        return message
    
    def _format_confirmation_buttons(self, question: str) -> str:
        """
        Format a yes/no question with confirmation buttons.
        
        Args:
            question (str): Question to ask
            
        Returns:
            str: Formatted message with keyboard
        """
        # Create keyboard buttons
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Yes", "callback_data": "yes"},
                    {"text": "No", "callback_data": "no"}
                ]
            ]
        }
        
        # Convert keyboard to JSON string and attach to the message
        import json
        message = question
        message += f"\n<<keyboard:{json.dumps(keyboard)}>>"
        
        return message
    
    def _process_duration_and_date(self, message_text: str) -> tuple:
        """
        Process the combined duration and travel date response.
        
        Args:
            message_text (str): Message text from the user
            
        Returns:
            tuple: (duration, travel_month)
        """
        import re
        message_lower = message_text.lower()
        
        # Extract duration (number of days)
        numbers = re.findall(r'\d+', message_text)
        duration = int(numbers[0]) if numbers else 7  # Default to 7 days
        
        # Extract month
        months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        # Check for month names
        travel_month = None
        for month in months:
            if month in message_lower or month[:3] in message_lower:
                travel_month = month.capitalize()
                break
                
        # Check for seasons if no month found
        if not travel_month:
            if any(season in message_lower for season in ['spring', 'april', 'may']):
                travel_month = 'April'
            elif any(season in message_lower for season in ['summer', 'july', 'august']):
                travel_month = 'July'
            elif any(season in message_lower for season in ['fall', 'autumn', 'october', 'november']):
                travel_month = 'October'
            elif any(season in message_lower for season in ['winter', 'january', 'february']):
                travel_month = 'January'
            else:
                # Default to current month+3
                from datetime import datetime
                current_month = datetime.now().month
                target_month = (current_month + 3) % 12
                if target_month == 0:
                    target_month = 12
                travel_month = months[target_month - 1].capitalize()
        
        return duration, travel_month
    
    def _update_festival_dates(self, recommendations: List[Dict[str, Any]], travel_month: str = None) -> List[Dict[str, Any]]:
        """
        Update festival dates to use current or upcoming year instead of hardcoded years.
        
        Args:
            recommendations (list): List of festival recommendations
            travel_month (str): User's preferred travel month
            
        Returns:
            list: Updated recommendations
        """
        from datetime import datetime
        
        # Get current date
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # Clone the recommendations to avoid modifying the original data
        updated_recommendations = []
        
        for rec in recommendations:
            # Clone the recommendation
            updated_rec = rec.copy()
            
            # Get festival month (from dates field)
            festival_dates = updated_rec.get('dates', '')
            festival_month = None
            
            # Extract month from dates field
            months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            for i, month in enumerate(months):
                if month in festival_dates or month.lower() in festival_dates:
                    festival_month = i + 1  # 1-indexed month
                    break
                
            if not festival_month:
                # Try with shortened month names
                for i, month in enumerate(months):
                    if month[:3] in festival_dates:
                        festival_month = i + 1
                        break
            
            # Determine appropriate year
            festival_year = current_year
            
            # If festival month is earlier than current month, use next year
            if festival_month and festival_month < current_month:
                festival_year = current_year + 1
                
            # If user's preferred travel month is specified, align with that
            if travel_month:
                user_month = None
                for i, month in enumerate(months):
                    if month.lower() == travel_month.lower():
                        user_month = i + 1
                        break
                
                if user_month:
                    # If user's month is this year or next year
                    if user_month < current_month:
                        # User wants to travel next year
                        festival_year = current_year + 1
                    else:
                        # User wants to travel this year
                        festival_year = current_year
            
            # Update the name and description with the year
            if 'name' in updated_rec:
                # Extract dates from festival dates field
                import re
                date_pattern = r'\((.*?)\d+.*?\)'
                date_match = re.search(date_pattern, festival_dates)
                
                if date_match:
                    date_info = date_match.group(1).strip()
                    
                    # Check if there are specific dates
                    day_pattern = r'(\d+)(st|nd|rd|th)'
                    day_matches = re.findall(day_pattern, festival_dates)
                    
                    if day_matches:
                        day_numbers = [m[0] for m in day_matches]
                        if len(day_numbers) >= 2:
                            # Format: Name (Month Day-Day, Year)
                            days_range = f"{day_numbers[0]}-{day_numbers[-1]}"
                            updated_rec['name'] = f"{updated_rec['name']} ({months[festival_month-1]} {days_range}, {festival_year})"
                        else:
                            # Format: Name (Month Day, Year)
                            updated_rec['name'] = f"{updated_rec['name']} ({months[festival_month-1]} {day_numbers[0]}, {festival_year})"
                    else:
                        # Format: Name (Month Year)
                        updated_rec['name'] = f"{updated_rec['name']} ({months[festival_month-1]} {festival_year})"
                else:
                    if festival_month:
                        # Just append the year if we at least know the month
                        updated_rec['name'] = f"{updated_rec['name']} ({months[festival_month-1]} {festival_year})"
            
            updated_recommendations.append(updated_rec)
        
        return updated_recommendations 