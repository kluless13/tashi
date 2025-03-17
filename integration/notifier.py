"""
Notifier for sending finalized travel plans to the Breathe Bhutan team.
"""
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List, Union
import requests

import config
from utils.logger import get_logger

logger = get_logger("business_notifier")

class BusinessNotifier:
    """
    Notifier for sending finalized travel plans to the Breathe Bhutan team.
    """
    
    def __init__(self, email: str = None, password: str = None, recipient: str = None):
        """
        Initialize the business notifier.
        
        Args:
            email (str): Email address to send from
            password (str): Email password
            recipient (str): Recipient email address
        """
        self.email = email or config.EMAIL_SENDER
        self.password = password or config.EMAIL_PASSWORD
        self.recipient = recipient or config.BREATHE_BHUTAN_EMAIL
        
        logger.info("BusinessNotifier initialized")
    
    def send_plan_via_email(self, user_info: Dict[str, str], 
                         preferences: Dict[str, Any], 
                         selected_plan: Dict[str, Any]) -> bool:
        """
        Send a finalized travel plan to the business via email.
        
        Args:
            user_info (dict): User information (name, email)
            preferences (dict): User preferences
            selected_plan (dict): Selected travel plan
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Sending travel plan via email for user {user_info.get('name')}")
        
        if not self.email or not self.password:
            logger.error("Email credentials not configured")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.recipient
            msg['Subject'] = f"New Travel Plan Request from {user_info.get('name')}"
            
            # Email body
            body = self._format_email_body(user_info, preferences, selected_plan)
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {self.recipient}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_plan_via_api(self, user_info: Dict[str, str], 
                        preferences: Dict[str, Any], 
                        selected_plan: Dict[str, Any],
                        api_url: str = None) -> bool:
        """
        Send a finalized travel plan to the business via API.
        
        Args:
            user_info (dict): User information (name, email)
            preferences (dict): User preferences
            selected_plan (dict): Selected travel plan
            api_url (str): API endpoint URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Sending travel plan via API for user {user_info.get('name')}")
        
        if not api_url:
            logger.error("API URL not specified")
            return False
        
        try:
            # Create payload
            payload = {
                'user_info': user_info,
                'preferences': preferences,
                'selected_plan': selected_plan,
                'timestamp': self._get_current_timestamp()
            }
            
            # Send request with retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(api_url, json=payload, timeout=30)
                    response.raise_for_status()
                    
                    logger.info(f"Plan sent successfully via API: {response.status_code}")
                    return True
                
                except requests.exceptions.RequestException as e:
                    logger.warning(f"API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                    
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Failed to send plan via API after {max_retries} attempts")
                        raise
            
            return False
        
        except Exception as e:
            logger.error(f"Error sending plan via API: {str(e)}")
            return False
    
    def notify_business(self, user_info: Dict[str, str], 
                         preferences: Dict[str, Any], 
                         selected_plan: Dict[str, Any],
                         api_url: str = None) -> bool:
        """
        Notify the business of a new travel plan using all available methods.
        
        Args:
            user_info (dict): User information (name, email)
            preferences (dict): User preferences
            selected_plan (dict): Selected travel plan
            api_url (str): API endpoint URL (optional)
            
        Returns:
            bool: True if at least one method was successful, False otherwise
        """
        # Try email first
        email_success = self.send_plan_via_email(user_info, preferences, selected_plan)
        
        # Try API if configured
        api_success = False
        if api_url:
            api_success = self.send_plan_via_api(user_info, preferences, selected_plan, api_url)
        
        # Log outcome
        if email_success or api_success:
            logger.info(f"Successfully notified business for user {user_info.get('name')}")
            return True
        else:
            logger.error(f"Failed to notify business for user {user_info.get('name')}")
            return False
    
    def _format_email_body(self, user_info: Dict[str, str], 
                           preferences: Dict[str, Any], 
                           selected_plan: Dict[str, Any]) -> str:
        """
        Format the email body.
        
        Args:
            user_info (dict): User information (name, email)
            preferences (dict): User preferences
            selected_plan (dict): Selected travel plan
            
        Returns:
            str: Formatted email body
        """
        # Format user information
        body = "NEW TRAVEL PLAN REQUEST\n"
        body += "=======================\n\n"
        
        body += "USER INFORMATION:\n"
        body += f"Name: {user_info.get('name', 'Not provided')}\n"
        body += f"Email: {user_info.get('email', 'Not provided')}\n\n"
        
        # Format preferences
        body += "PREFERENCES:\n"
        body += f"Trip Type: {preferences.get('trip_type', 'Not specified')}\n"
        body += f"Duration: {preferences.get('duration', 'Not specified')} days\n"
        body += f"Travel Month: {preferences.get('travel_month', 'Not specified')}\n"
        
        interests = preferences.get('interests', [])
        if interests:
            body += f"Interests: {', '.join(interests)}\n\n"
        else:
            body += "Interests: Not specified\n\n"
        
        # Format selected plan
        body += "SELECTED TRAVEL PLAN:\n"
        body += f"Title: {selected_plan.get('title', 'Not specified')}\n"
        body += f"Duration: {selected_plan.get('duration', 'Not specified')}\n"
        
        description = selected_plan.get('description', selected_plan.get('summary', 'Not specified'))
        body += f"Description: {description}\n\n"
        
        # Add highlights if available
        highlights = selected_plan.get('highlights', [])
        if highlights:
            body += "Highlights:\n"
            for highlight in highlights:
                body += f"- {highlight}\n"
            body += "\n"
        
        # Add itinerary if available
        itinerary = selected_plan.get('itinerary', [])
        if itinerary:
            body += "Itinerary:\n"
            for day in itinerary:
                body += f"{day.get('day', 'Day')}: {day.get('description', 'No description')}\n"
            body += "\n"
        
        body += "Please contact the user to confirm the travel plan and provide additional details.\n"
        body += f"This request was generated by the Tashi bot at {self._get_current_timestamp()}."
        
        return body
    
    def _get_current_timestamp(self) -> str:
        """
        Get the current timestamp as a string.
        
        Returns:
            str: Current timestamp
        """
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 