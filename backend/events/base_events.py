from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    # Game Events
    GAME_CREATED = "game.created"
    GAME_UPDATED = "game.updated"
    GAME_DELETED = "game.deleted"
    
    # Player Events
    PLAYER_JOINED = "player.joined"
    PLAYER_LEFT = "player.left"
    PLAYER_ACTION = "player.action"
    
    # State Events
    STATE_CHANGED = "state.changed"
    STATE_SAVED = "state.saved"
    STATE_RESTORED = "state.restored"
    
    # Chat Events
    MESSAGE_SENT = "chat.message_sent"
    MESSAGE_RECEIVED = "chat.message_received"
    
    # Rule Events
    RULE_TRIGGERED = "rule.triggered"
    RULE_VALIDATED = "rule.validated"
    
    # System Events
    MODULE_LOADED = "system.module_loaded"
    MODULE_ERROR = "system.module_error"

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    source_module: str
    game_id: Optional[str] = None
    player_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GameEvent(BaseEvent):
    game_name: str
    game_config: Dict[str, Any]

class PlayerEvent(BaseEvent):
    player_name: str
    action: Optional[str] = None

class StateEvent(BaseEvent):
    state_key: str
    old_state: Optional[Dict[str, Any]] = None
    new_state: Dict[str, Any]

class ChatEvent(BaseEvent):
    message: str
    bot_id: str
    response: Optional[str] = None

class RuleEvent(BaseEvent):
    rule_name: str
    rule_result: bool
    details: Dict[str, Any]