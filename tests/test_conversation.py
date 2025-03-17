"""
Tests for the conversation module.
"""
import unittest
from unittest.mock import patch, MagicMock

import config
from bot.conversation import ConversationManager, ConversationState

class TestConversationManager(unittest.TestCase):
    """
    Test cases for the ConversationManager class.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        """
        self.conversation_manager = ConversationManager()
        
        # Sample user ID for testing
        self.user_id = 123456789
    
    def test_start_conversation(self):
        """
        Test starting a new conversation.
        """
        # Start a new conversation
        response = self.conversation_manager.start_conversation(self.user_id)
        
        # Verify that the conversation is initialized correctly
        self.assertIn(self.user_id, self.conversation_manager.conversations)
        self.assertEqual(self.conversation_manager.conversations[self.user_id]['state'], ConversationState.GREETING)
        self.assertEqual(response, config.WELCOME_MESSAGE)
    
    def test_process_message_greeting(self):
        """
        Test processing a message in the GREETING state.
        """
        # Start a new conversation
        self.conversation_manager.start_conversation(self.user_id)
        
        # Process a message in the GREETING state
        response = self.conversation_manager.process_message(self.user_id, "Hello!")
        
        # Verify that the state transitions to TRIP_TYPE
        self.assertEqual(self.conversation_manager.conversations[self.user_id]['state'], ConversationState.TRIP_TYPE)
        self.assertEqual(response, config.TRIP_TYPE_PROMPT)
    
    def test_process_message_trip_type(self):
        """
        Test processing a message in the TRIP_TYPE state.
        """
        # Set up the conversation in the TRIP_TYPE state
        self.conversation_manager.start_conversation(self.user_id)
        self.conversation_manager.conversations[self.user_id]['state'] = ConversationState.TRIP_TYPE
        
        # Process a message in the TRIP_TYPE state
        response = self.conversation_manager.process_message(self.user_id, "I'm interested in cultural tours")
        
        # Verify that the state transitions to DURATION
        self.assertEqual(self.conversation_manager.conversations[self.user_id]['state'], ConversationState.DURATION)
        self.assertEqual(self.conversation_manager.conversations[self.user_id]['preferences']['trip_type'], 'cultural')
        self.assertEqual(response, config.DURATION_PROMPT)
    
    def test_process_duration(self):
        """
        Test processing a duration message.
        """
        # Test with a numeric duration
        duration = self.conversation_manager._process_duration("I want to stay for 7 days")
        self.assertEqual(duration, 7)
        
        # Test with a non-numeric message
        duration = self.conversation_manager._process_duration("I'm not sure how long")
        self.assertEqual(duration, 7)  # Default value
    
    def test_process_travel_date(self):
        """
        Test processing a travel date message.
        """
        # Test with a month name
        month = self.conversation_manager._process_travel_date("I want to travel in October")
        self.assertEqual(month, "October")
        
        # Test with a season
        month = self.conversation_manager._process_travel_date("I'm thinking of traveling in the spring")
        self.assertEqual(month, "April")  # Middle of spring
    
    def test_process_interests(self):
        """
        Test processing an interests message.
        """
        # Test with common interests
        interests = self.conversation_manager._process_interests("I'm interested in hiking, culture, and photography")
        self.assertIn("hiking", interests)
        self.assertIn("culture", interests)
        self.assertIn("photography", interests)
        
        # Test with no recognized interests
        interests = self.conversation_manager._process_interests("I want something fun")
        self.assertEqual(interests, ["culture", "nature"])  # Default interests
    
    def test_is_affirmative(self):
        """
        Test the affirmative response checker.
        """
        self.assertTrue(self.conversation_manager._is_affirmative("Yes, I like that plan"))
        self.assertTrue(self.conversation_manager._is_affirmative("Sure, sounds good"))
        self.assertFalse(self.conversation_manager._is_affirmative("No, I don't like it"))
    
    def test_is_negative(self):
        """
        Test the negative response checker.
        """
        self.assertTrue(self.conversation_manager._is_negative("No, I don't like that"))
        self.assertTrue(self.conversation_manager._is_negative("I want something different"))
        self.assertFalse(self.conversation_manager._is_negative("Yes, that's perfect"))
    
    def test_end_conversation(self):
        """
        Test ending a conversation.
        """
        # Start a conversation
        self.conversation_manager.start_conversation(self.user_id)
        
        # Verify that the conversation exists
        self.assertIn(self.user_id, self.conversation_manager.conversations)
        
        # End the conversation
        self.conversation_manager.end_conversation(self.user_id)
        
        # Verify that the conversation is removed
        self.assertNotIn(self.user_id, self.conversation_manager.conversations)
    
    def test_serialize_deserialize(self):
        """
        Test serializing and deserializing conversations.
        """
        # Start a conversation
        self.conversation_manager.start_conversation(self.user_id)
        self.conversation_manager.conversations[self.user_id]['preferences'] = {'trip_type': 'cultural'}
        
        # Serialize conversations
        serialized = self.conversation_manager.serialize_conversations()
        
        # Create a new conversation manager
        new_manager = ConversationManager()
        
        # Deserialize conversations
        new_manager.deserialize_conversations(serialized)
        
        # Verify that the conversation is restored
        self.assertIn(self.user_id, new_manager.conversations)
        self.assertEqual(new_manager.conversations[self.user_id]['state'].name, ConversationState.GREETING.name)
        self.assertEqual(new_manager.conversations[self.user_id]['preferences']['trip_type'], 'cultural')

if __name__ == '__main__':
    unittest.main() 