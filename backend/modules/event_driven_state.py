from faststream import FastStream, Context
from faststream.redis import RedisBroker
from events.base_events import BaseEvent, StateEvent, EventType
from modules.state_management import StateManager, StateConfig
from typing import Dict

broker = RedisBroker("redis://localhost:6379")
app = FastStream(broker)

class StateService:
    def __init__(self):
        config = StateConfig(auto_save=True, storage_type="redis")
        self.state_manager = StateManager(config)
        self.active_games: Dict[str, str] = {}  # game_id -> status

state_service = StateService()

@broker.subscriber("player.action")
async def handle_player_action(event: BaseEvent):
    """Handle player actions that affect game state"""
    if not event.game_id or not event.player_id:
        return
    
    action_data = event.data
    current_state = await state_service.state_manager.get_state(event.game_id, event.player_id)
    
    # Process action based on type
    state_updates = {}
    
    if action_data.get("type") == "move":
        state_updates["position"] = action_data.get("position", {})
        state_updates["last_move"] = event.timestamp.isoformat()
    
    elif action_data.get("type") == "inventory":
        current_inventory = current_state.state_data.get("inventory", []) if current_state else []
        if action_data.get("action") == "add_item":
            current_inventory.append(action_data.get("item"))
        elif action_data.get("action") == "remove_item":
            if action_data.get("item") in current_inventory:
                current_inventory.remove(action_data.get("item"))
        state_updates["inventory"] = current_inventory
    
    elif action_data.get("type") == "stats":
        current_stats = current_state.state_data.get("stats", {}) if current_state else {}
        current_stats.update(action_data.get("stats", {}))
        state_updates["stats"] = current_stats
    
    # Update state
    if state_updates:
        old_state = current_state.state_data if current_state else {}
        updated_state = await state_service.state_manager.update_state(
            event.game_id, event.player_id, state_updates
        )
        
        # Publish state change event
        state_event = StateEvent(
            event_type=EventType.STATE_CHANGED,
            source_module="state_service",
            game_id=event.game_id,
            player_id=event.player_id,
            state_key=f"{event.game_id}:{event.player_id}",
            old_state=old_state,
            new_state=updated_state.state_data
        )
        
        await broker.publish(state_event, "state.changed")

@broker.subscriber("game.created")
async def handle_game_created(event: BaseEvent):
    """Initialize game state when game is created"""
    state_service.active_games[event.game_id] = "active"
    
    # Create initial state for game creator
    initial_state = {
        "game_created_at": event.timestamp.isoformat(),
        "game_config": event.data.get("game_config", {}),
        "status": "active"
    }
    
    creator_id = event.data.get("creator_id", "system")
    await state_service.state_manager.update_state(
        event.game_id, creator_id, initial_state
    )

@broker.subscriber("state.save_request")
async def handle_save_request(event: BaseEvent):
    """Handle manual save requests"""
    if event.game_id and event.player_id:
        current_state = await state_service.state_manager.get_state(event.game_id, event.player_id)
        if current_state:
            await state_service.state_manager.storage.save(
                f"{event.game_id}:{event.player_id}", current_state
            )
            
            # Publish save confirmation
            save_event = BaseEvent(
                event_type=EventType.STATE_SAVED,
                source_module="state_service",
                game_id=event.game_id,
                player_id=event.player_id,
                data={"saved_at": event.timestamp.isoformat()}
            )
            
            await broker.publish(save_event, "state.saved")

if __name__ == "__main__":
    app.run()