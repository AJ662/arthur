from faststream import FastStream
from faststream.redis import RedisBroker
from events.base_events import BaseEvent, RuleEvent, EventType
from pydantic import BaseModel
from typing import Dict, List, Any, Callable

broker = RedisBroker("redis://localhost:6379")
app = FastStream(broker)

class Rule(BaseModel):
    name: str
    condition: str  # Python expression as string
    action: str     # Action to take when rule triggers
    priority: int = 1
    enabled: bool = True
    game_id: Optional[str] = None

class RuleEngine:
    def __init__(self):
        self.rules: Dict[str, List[Rule]] = {}  # game_id -> rules
        self.global_rules: List[Rule] = []
    
    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        if rule.game_id:
            if rule.game_id not in self.rules:
                self.rules[rule.game_id] = []
            self.rules[rule.game_id].append(rule)
        else:
            self.global_rules.append(rule)
    
    def evaluate_rules(self, game_id: str, context: Dict[str, Any]) -> List[RuleEvent]:
        """Evaluate all applicable rules for a game"""
        triggered_events = []
        
        # Get applicable rules
        applicable_rules = self.global_rules[:]
        if game_id in self.rules:
            applicable_rules.extend(self.rules[game_id])
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            
            try:
                # Evaluate condition
                result = eval(rule.condition, {"__builtins__": {}}, context)
                
                if result:
                    # Rule triggered
                    rule_event = RuleEvent(
                        event_type=EventType.RULE_TRIGGERED,
                        source_module="rule_engine",
                        game_id=game_id,
                        rule_name=rule.name,
                        rule_result=True,
                        details={
                            "condition": rule.condition,
                            "action": rule.action,
                            "context": context
                        }
                    )
                    triggered_events.append(rule_event)
                
            except Exception as e:
                # Log error but continue
                error_event = BaseEvent(
                    event_type=EventType.MODULE_ERROR,
                    source_module="rule_engine",
                    game_id=game_id,
                    data={
                        "error": f"Rule evaluation failed: {rule.name}",
                        "exception": str(e)
                    }
                )
                triggered_events.append(error_event)
        
        return triggered_events

rule_engine = RuleEngine()

@app.on_startup
async def setup_default_rules():
    """Setup default game rules"""
    # Victory condition rule
    victory_rule = Rule(
        name="check_victory",
        condition="context.get('score', 0) >= 100",
        action="trigger_victory",
        priority=10
    )
    rule_engine.add_rule(victory_rule)
    
    # Health check rule
    health_rule = Rule(
        name="check_health",
        condition="context.get('health', 100) <= 0",
        action="trigger_game_over",
        priority=9
    )
    rule_engine.add_rule(health_rule)

@broker.subscriber("state.changed")
async def evaluate_on_state_change(event: StateEvent):
    """Evaluate rules when state changes"""
    if not event.game_id:
        return
    
    # Create evaluation context
    context = {
        "state": event.new_state,
        "old_state": event.old_state or {},
        "player_id": event.player_id,
        "timestamp": event.timestamp.timestamp(),
        **event.new_state  # Include state data directly in context
    }
    
    # Evaluate rules
    triggered_events = rule_engine.evaluate_rules(event.game_id, context)
    
    # Publish triggered rule events
    for rule_event in triggered_events:
        await broker.publish(rule_event, "rules.triggered")

@broker.subscriber("player.action")
async def evaluate_on_player_action(event: BaseEvent):
    """Evaluate rules on player actions"""
    if not event.game_id:
        return
    
    context = {
        "action": event.data,
        "player_id": event.player_id,
        "timestamp": event.timestamp.timestamp(),
        **event.data
    }
    
    triggered_events = rule_engine.evaluate_rules(event.game_id, context)
    
    for rule_event in triggered_events:
        await broker.publish(rule_event, "rules.triggered")

@broker.subscriber("rules.add")
async def add_new_rule(event: BaseEvent):
    """Add new rules dynamically"""
    rule_data = event.data.get("rule")
    if rule_data:
        rule = Rule(**rule_data)
        rule_engine.add_rule(rule)

if __name__ == "__main__":
    app.run()