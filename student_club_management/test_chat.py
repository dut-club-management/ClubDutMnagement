#!/usr/bin/env python3
import os, sys
import requests
import json

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app, db
from models.user import User
from models.chat import ChatConversation, ChatMessage

def test_chat_functionality():
    """Test chat functionality"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Chat Functionality")
        print("=" * 40)
        
        # Test 1: Check if users exist for chat
        print("✅ 1. Testing Users...")
        users = User.query.all()
        if len(users) >= 2:
            print(f"   ✅ Found {len(users)} users for testing")
        else:
            print(f"   ❌ Need at least 2 users, found {len(users)}")
            return False
        
        # Test 2: Create a test conversation
        print("✅ 2. Creating Test Conversation...")
        user1 = users[0]
        user2 = users[1]
        
        # Check if conversation already exists
        existing_conv = ChatConversation.query.filter(
            (ChatConversation.participant_one == user1.id) & (ChatConversation.participant_two == user2.id) |
            (ChatConversation.participant_one == user2.id) & (ChatConversation.participant_two == user1.id)
        ).first()
        
        if not existing_conv:
            conversation = ChatConversation(
                created_by=user1.id,
                participant_one=user1.id,
                participant_two=user2.id,
                subject="Test Conversation"
            )
            db.session.add(conversation)
            db.session.commit()
            print(f"   ✅ Created conversation between {user1.first_name} and {user2.first_name}")
        else:
            conversation = existing_conv
            print(f"   ✅ Using existing conversation")
        
        # Test 3: Create test message
        print("✅ 3. Creating Test Message...")
        message = ChatMessage(
            conversation_id=conversation.id,
            sender_id=user1.id,
            recipient_id=user2.id,
            message="Hello! This is a test message."
        )
        db.session.add(message)
        db.session.commit()
        print(f"   ✅ Created test message")
        
        # Test 4: Verify message can be retrieved
        print("✅ 4. Testing Message Retrieval...")
        messages = ChatMessage.query.filter_by(conversation_id=conversation.id).all()
        print(f"   ✅ Found {len(messages)} messages in conversation")
        
        for msg in messages:
            print(f"      - {msg.sender.first_name}: {msg.message}")
        
        print("\n🎉 Chat functionality is working!")
        print("=" * 40)
        print("📝 Test Results:")
        print(f"   - Users: {len(users)}")
        print(f"   - Conversation ID: {conversation.id}")
        print(f"   - Messages: {len(messages)}")
        print(f"   - Last message: {messages[-1].message}")
        
        print("\n🌐 You can now test chat in the browser:")
        print(f"   - Login as: {user1.email}")
        print(f"   - Go to: http://127.0.0.1:5000/chat")
        print(f"   - Start conversation with: {user2.first_name} {user2.last_name}")
        
        return True

if __name__ == '__main__':
    test_chat_functionality()
