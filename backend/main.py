from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
import json
from datetime import datetime
import google.generativeai as genai
import aiofiles
import os

# Configure Gemini
genai.configure(api_key="AIzaSyADGdj8ZO4utxYiOqkcnUEuXjrrTHh-H94")

app = FastAPI(title="Multi-Bot Game System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CreateGameRequest(BaseModel):
    name: str
    bots: List[str] = Field(default=["game_master", "npc_wizard", "helper"])

class ChatRequest(BaseModel):
    message: str
    game_id: str
    player_id: str = "player1"

class AddBotRequest(BaseModel):
    bot_type: str
    name: str
    personality: str
    system_prompt: str

# Simple file-based storage
GAMES_DIR = "./game_data"
os.makedirs(GAMES_DIR, exist_ok=True)

# Bot templates
BOT_TEMPLATES = {
    "game_master": {
        "name": "Game Master",
        "personality": "Wise and guiding narrator who describes the world and guides the adventure.",
        "system_prompt": "You are the Game Master. Describe scenes, narrate events, and guide the adventure. Always respond in character."
    },
    "npc_wizard": {
        "name": "Eldor the Wizard",  
        "personality": "Mysterious wizard with ancient knowledge, speaks cryptically.",
        "system_prompt": "You are Eldor, an ancient wizard. You speak in riddles and offer cryptic advice. You know ancient magic and lore."
    },
    "npc_merchant": {
        "name": "Trader Bob",
        "personality": "Cheerful merchant who loves to bargain and trade.",
        "system_prompt": "You are Bob, a traveling merchant. You're always trying to sell something and love a good deal."
    },
    "helper": {
        "name": "Guide",
        "personality": "Helpful assistant who explains game mechanics.",
        "system_prompt": "You are a helpful guide. Explain game mechanics and help players understand what's happening."
    }
}

model = genai.GenerativeModel('gemini-2.0-flash-exp')

async def save_game_state(game_id: str, state: dict):
    """Save game state to file"""
    file_path = f"{GAMES_DIR}/{game_id}.json"
    async with aiofiles.open(file_path, 'w') as f:
        await f.write(json.dumps(state, indent=2, default=str))

async def load_game_state(game_id: str) -> dict:
    """Load game state from file"""
    file_path = f"{GAMES_DIR}/{game_id}.json"
    try:
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except FileNotFoundError:
        return None

@app.post("/games/")
async def create_game(request: CreateGameRequest):
    """Create a new game with multiple bots"""
    game_id = str(uuid.uuid4())
    
    # Create bots for this game
    game_bots = {}
    for bot_type in request.bots:
        if bot_type in BOT_TEMPLATES:
            template = BOT_TEMPLATES[bot_type]
            game_bots[bot_type] = {
                **template,
                "conversation_history": [],
                "active": True
            }
    
    # Initial game state
    game_state = {
        "id": game_id,
        "name": request.name,
        "created_at": datetime.now().isoformat(),
        "bots": game_bots,
        "shared_context": {
            "scene": "A mystical tavern where adventurers gather",
            "player_status": "healthy",
            "inventory": [],
            "current_location": "tavern"
        },
        "conversation_log": [],  # All messages across all bots
        "last_updated": datetime.now().isoformat()
    }
    
    await save_game_state(game_id, game_state)
    
    return {"game_id": game_id, "bots": list(game_bots.keys()), "status": "created"}

@app.post("/games/{game_id}/chat")
async def multi_bot_chat(game_id: str, request: ChatRequest):
    """Send message and get responses from ALL active bots"""
    
    # Load game state
    game_state = await load_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Add player message to conversation log
    player_message = {
        "id": str(uuid.uuid4()),
        "sender": "player",
        "sender_name": request.player_id,
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    }
    game_state["conversation_log"].append(player_message)
    
    # Generate responses from all active bots
    bot_responses = []
    
    for bot_id, bot_data in game_state["bots"].items():
        if not bot_data["active"]:
            continue
            
        try:
            # Build context for this bot
            context = f"""
{bot_data['system_prompt']}

Current Scene: {game_state['shared_context']['scene']}
Player Status: {game_state['shared_context']['player_status']}
Location: {game_state['shared_context']['current_location']}

Recent Conversation:
"""
            
            # Add recent conversation (last 10 messages)
            recent_messages = game_state["conversation_log"][-10:]
            for msg in recent_messages:
                if msg["sender"] == "player":
                    context += f"Player: {msg['content']}\n"
                else:
                    context += f"{msg['sender_name']}: {msg['content']}\n"
            
            context += f"\nPlayer just said: {request.message}\n\nRespond as {bot_data['name']} ({bot_data['personality']}):"
            
            # Generate response
            response = model.generate_content(
                context,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=200,
                )
            )
            
            bot_response_text = response.text.strip()
            
            # Create bot response
            bot_message = {
                "id": str(uuid.uuid4()),
                "sender": "bot",
                "sender_name": bot_data["name"],
                "bot_id": bot_id,
                "content": bot_response_text,
                "timestamp": datetime.now().isoformat()
            }
            
            game_state["conversation_log"].append(bot_message)
            bot_responses.append(bot_message)
            
        except Exception as e:
            print(f"Error generating response for {bot_id}: {e}")
            continue
    
    # Update game state timestamp
    game_state["last_updated"] = datetime.now().isoformat()
    
    # Save updated state
    await save_game_state(game_id, game_state)
    
    return {
        "player_message": player_message,
        "bot_responses": bot_responses,
        "game_state": game_state["shared_context"]
    }

@app.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get full game state"""
    game_state = await load_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_state

@app.get("/games/{game_id}/conversation")
async def get_conversation(game_id: str, limit: int = 50):
    """Get conversation history"""
    game_state = await load_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        "conversation": game_state["conversation_log"][-limit:],
        "active_bots": [{"id": k, "name": v["name"]} for k, v in game_state["bots"].items() if v["active"]]
    }

@app.post("/games/{game_id}/bots")
async def add_bot_to_game(game_id: str, request: AddBotRequest):
    """Add a custom bot to the game"""
    game_state = await load_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    bot_id = f"custom_{len(game_state['bots'])}"
    game_state["bots"][bot_id] = {
        "name": request.name,
        "personality": request.personality,
        "system_prompt": request.system_prompt,
        "conversation_history": [],
        "active": True
    }
    
    await save_game_state(game_id, game_state)
    return {"bot_id": bot_id, "status": "added"}

@app.put("/games/{game_id}/bots/{bot_id}/toggle")
async def toggle_bot(game_id: str, bot_id: str):
    """Enable/disable a bot"""
    game_state = await load_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if bot_id not in game_state["bots"]:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    game_state["bots"][bot_id]["active"] = not game_state["bots"][bot_id]["active"]
    await save_game_state(game_id, game_state)
    
    return {"bot_id": bot_id, "active": game_state["bots"][bot_id]["active"]}

@app.get("/bot-templates")
async def get_bot_templates():
    """Get available bot templates"""
    return BOT_TEMPLATES

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)