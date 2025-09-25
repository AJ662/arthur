import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import os

# Configure Gemini
genai.configure(api_key="AIzaSyADGdj8ZO4utxYiOqkcnUEuXjrrTHh-H94")

class ChatbotPersonality(str, Enum):
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    GAME_MASTER = "game_master"
    MENTOR = "mentor"
    CHARACTER = "character"

class ChatbotConfig(BaseModel):
    name: str
    personality: ChatbotPersonality
    system_prompt: str
    context_memory: int = Field(default=10, description="Number of messages to remember")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, gt=0)
    custom_instructions: Optional[str] = None
    game_context: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    role: str  # "user", "model"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class GeminiChatbot:
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.conversation_history: List[ChatMessage] = []
        self.game_context = config.game_context or {}
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Latest fastest model
        
        # Setup system prompt based on personality
        self.system_context = self._build_system_context()
    
    def _build_system_context(self) -> str:
        """Build comprehensive system context"""
        base_context = f"""
You are {self.config.name}, a {self.config.personality.value} AI assistant for a game development platform.

{self.config.system_prompt}

Personality Guidelines:
- {self.config.personality.value}: {self._get_personality_guide()}

Current Game Context: {json.dumps(self.game_context) if self.game_context else "No active game"}

Additional Instructions: {self.config.custom_instructions or "None"}

Keep responses engaging, helpful, and appropriate for game development and gaming contexts.
"""
        return base_context
    
    def _get_personality_guide(self) -> str:
        guides = {
            "friendly": "Be warm, encouraging, and supportive. Use casual language and show enthusiasm.",
            "professional": "Be precise, informative, and business-like. Provide structured responses.",
            "game_master": "Be creative, dramatic, and immersive. Guide players through adventures with vivid descriptions.",
            "mentor": "Be patient, educational, and encouraging. Help users learn and improve their skills.",
            "character": "Stay in character based on your role. Be consistent with your character's personality and background."
        }
        return guides.get(self.config.personality, "Be helpful and appropriate to the context.")
    
    async def process_message(self, message: str, user_id: str = None) -> str:
        """Process incoming message and return Gemini response"""
        try:
            # Build conversation context
            conversation_context = self.system_context + "\n\nConversation:\n"
            
            # Add recent history
            recent_history = self.conversation_history[-self.config.context_memory:]
            for msg in recent_history:
                role = "Human" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"
            
            # Add current message
            conversation_context += f"Human: {message}\nAssistant:"
            
            # Generate response using Gemini
            response = await self._generate_gemini_response(conversation_context, message)
            
            # Add messages to history
            user_msg = ChatMessage(
                role="user",
                content=message,
                timestamp=self._get_timestamp(),
                metadata={"user_id": user_id}
            )
            
            assistant_msg = ChatMessage(
                role="model",
                content=response,
                timestamp=self._get_timestamp()
            )
            
            self.conversation_history.extend([user_msg, assistant_msg])
            
            # Maintain context memory limit
            if len(self.conversation_history) > self.config.context_memory * 2:
                self.conversation_history = self.conversation_history[-self.config.context_memory * 2:]
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Pl