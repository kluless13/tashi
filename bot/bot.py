"""
Main Telegram bot functionality for the Tashi bot.
"""
import os
from typing import Dict, Any, Optional, List, Union, Callable

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, CallbackQueryHandler, ConversationHandler
)

import config
from utils.logger import get_logger
from bot.conversation import ConversationManager
from recommendation.engine import RecommendationEngine
from integration.notifier import BusinessNotifier

logger = get_logger("bot")

class TashiBot:
    """
    Main Telegram bot class for the Tashi bot.
    """
    
    def __init__(self, token: str = None):
        """
        Initialize the Telegram bot.
        
        Args:
            token (str): Telegram bot token
        """
        self.token = token or config.TELEGRAM_API_TOKEN
        self.application = Application.builder().token(self.token).build()
        
        # Initialize components
        self.conversation_manager = ConversationManager()
        self.recommendation_engine = RecommendationEngine()
        self.business_notifier = BusinessNotifier()
        
        # Set up handlers
        self._setup_handlers()
        
        logger.info("TashiBot initialized")
    
    def _setup_handlers(self) -> None:
        """
        Set up the message handlers.
        """
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("reset", self._handle_reset))
        
        # Message handler for regular text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Callback query handler for button clicks
        self.application.add_handler(CallbackQueryHandler(self._handle_button))
        
        # Error handler
        self.application.add_error_handler(self._handle_error)
        
        logger.info("Handlers set up")
    
    async def _handle_start(self, update: Update, context: CallbackContext) -> None:
        """
        Handle the /start command.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        logger.info(f"Received /start command from user {user_id} ({username})")
        
        # Start a new conversation
        response = self.conversation_manager.start_conversation(user_id)
        
        # Send the response
        await update.message.reply_text(response)
    
    async def _handle_help(self, update: Update, context: CallbackContext) -> None:
        """
        Handle the /help command.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context
        """
        help_message = """
I'm Tashi, your personal travel assistant for planning your trip to Bhutan.

Here's how I can help you:
- Plan a cultural tour in Bhutan
- Find festival dates and information
- Recommend trekking routes based on your preferences
- Create a custom itinerary for your travel dates

You can use the following commands:
/start - Start a new conversation
/help - Show this help message
/reset - Reset the current conversation

Just follow along with my questions, and I'll help you plan the perfect trip to Bhutan!
"""
        await update.message.reply_text(help_message)
    
    async def _handle_reset(self, update: Update, context: CallbackContext) -> None:
        """
        Handle the /reset command.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context
        """
        user_id = update.effective_user.id
        
        # End the current conversation
        self.conversation_manager.end_conversation(user_id)
        
        # Start a new conversation
        response = self.conversation_manager.start_conversation(user_id)
        
        # Send the response
        await update.message.reply_text("Conversation reset. Let's start over!\n\n" + response)
    
    async def _handle_message(self, update: Update, context: CallbackContext) -> None:
        """
        Handle regular text messages.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context
        """
        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.info(f"Received message from user {user_id}: {message_text}")
        
        # Process the message through the conversation manager
        response = self.conversation_manager.process_message(user_id, message_text)
        
        # Check if the response contains an inline keyboard markup
        keyboard_markup = None
        if '<<keyboard:' in response:
            # Extract the keyboard JSON and create a proper InlineKeyboardMarkup
            import json
            import re
            
            keyboard_match = re.search(r'<<keyboard:(.*?)>>', response)
            if keyboard_match:
                keyboard_json = keyboard_match.group(1)
                keyboard_dict = json.loads(keyboard_json)
                
                # Create buttons from the keyboard dictionary
                keyboard = []
                for row in keyboard_dict.get('inline_keyboard', []):
                    keyboard_row = []
                    for button in row:
                        keyboard_row.append(InlineKeyboardButton(
                            text=button.get('text', ''),
                            callback_data=button.get('callback_data', '')
                        ))
                    keyboard.append(keyboard_row)
                
                # Create the inline keyboard markup
                keyboard_markup = InlineKeyboardMarkup(keyboard)
                
                # Remove the keyboard tag from the response
                response = re.sub(r'<<keyboard:.*?>>', '', response).strip()
        
        # Send the response with keyboard if present
        if keyboard_markup:
            await update.message.reply_text(response, reply_markup=keyboard_markup)
        else:
            await update.message.reply_text(response)
    
    async def _handle_button(self, update: Update, context: CallbackContext) -> None:
        """
        Handle button clicks from inline keyboards.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context
        """
        query = update.callback_query
        await query.answer()  # Answer the callback query to remove the "loading" state
        
        user_id = update.effective_user.id
        callback_data = query.data
        
        logger.info(f"Received button click from user {user_id}: {callback_data}")
        
        # Process the callback data through the conversation manager
        response = self.conversation_manager.process_message(user_id, callback_data)
        
        # Check if the response contains an inline keyboard markup
        keyboard_markup = None
        if '<<keyboard:' in response:
            # Extract the keyboard JSON and create a proper InlineKeyboardMarkup
            import json
            import re
            
            keyboard_match = re.search(r'<<keyboard:(.*?)>>', response)
            if keyboard_match:
                keyboard_json = keyboard_match.group(1)
                keyboard_dict = json.loads(keyboard_json)
                
                # Create buttons from the keyboard dictionary
                keyboard = []
                for row in keyboard_dict.get('inline_keyboard', []):
                    keyboard_row = []
                    for button in row:
                        keyboard_row.append(InlineKeyboardButton(
                            text=button.get('text', ''),
                            callback_data=button.get('callback_data', '')
                        ))
                    keyboard.append(keyboard_row)
                
                # Create the inline keyboard markup
                keyboard_markup = InlineKeyboardMarkup(keyboard)
                
                # Remove the keyboard tag from the response
                response = re.sub(r'<<keyboard:.*?>>', '', response).strip()
        
        # Update the message with the new response and keyboard if present
        if keyboard_markup:
            await query.edit_message_text(text=response, reply_markup=keyboard_markup)
        else:
            await query.edit_message_text(text=response)
    
    async def _handle_error(self, update: Update, context: CallbackContext) -> None:
        """
        Handle errors that occur during the processing of updates.
        
        Args:
            update (Update): Telegram update
            context (CallbackContext): Callback context with error
        """
        logger.error(f"Error occurred: {context.error}")
        
        # Send error message to user
        if update and update.effective_user:
            await update.effective_message.reply_text(config.ERROR_MESSAGE)
    
    def start(self) -> None:
        """
        Start the bot.
        """
        logger.info("Starting bot")
        self.application.run_polling()
        logger.info("Bot started")
    
    def stop(self) -> None:
        """
        Stop the bot.
        """
        logger.info("Stopping bot")
        self.application.stop()
        logger.info("Bot stopped")
    
    def save_state(self, file_path: str) -> None:
        """
        Save the bot state to a file.
        
        Args:
            file_path (str): Path to save the state to
        """
        try:
            # Serialize conversations
            conversations_json = self.conversation_manager.serialize_conversations()
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(conversations_json)
            
            logger.info(f"Bot state saved to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving bot state: {str(e)}")
    
    def load_state(self, file_path: str) -> bool:
        """
        Load the bot state from a file.
        
        Args:
            file_path (str): Path to load the state from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"State file does not exist: {file_path}")
                return False
            
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                conversations_json = f.read()
            
            # Deserialize conversations
            self.conversation_manager.deserialize_conversations(conversations_json)
            
            logger.info(f"Bot state loaded from {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading bot state: {str(e)}")
            return False
    
    def get_webhook_url(self, base_url: str) -> str:
        """
        Get the webhook URL for the bot.
        
        Args:
            base_url (str): Base URL for the webhook
            
        Returns:
            str: Webhook URL
        """
        return f"{base_url}/bot{self.token}"
    
    def set_webhook(self, webhook_url: str) -> bool:
        """
        Set up a webhook for the bot.
        
        Args:
            webhook_url (str): URL to receive webhook updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.application.bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to {webhook_url}")
            return True
        
        except Exception as e:
            logger.error(f"Error setting webhook: {str(e)}")
            return False
    
    def remove_webhook(self) -> bool:
        """
        Remove the webhook for the bot.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.application.bot.delete_webhook()
            logger.info("Webhook removed")
            return True
        
        except Exception as e:
            logger.error(f"Error removing webhook: {str(e)}")
            return False


if __name__ == "__main__":
    """
    Run the bot as a standalone script.
    """
    bot = TashiBot()
    bot.start() 