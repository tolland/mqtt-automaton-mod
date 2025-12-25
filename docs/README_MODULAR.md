# Modular Bot Architecture

This document describes the new modular architecture for the Minecraft bot system, designed to be more maintainable, extensible, and easier to understand than the original monolithic approach.

## Overview

The modular architecture separates concerns into distinct, reusable components:

- **Behaviors**: Modular units that handle specific bot activities (farming, mining, emergency response)
- **Patterns**: Reusable movement and action sequences
- **Events**: Handlers for game events (pillager attacks, player detection)
- **Core**: Framework components that orchestrate everything

## Architecture

```
scripts/
├── core/                           # Core bot framework
│   ├── behavior_engine.py          # Orchestrates behaviors
│   └── modular_bot_client.py       # Main bot client
├── behaviors/                      # Modular behaviors
│   ├── base_behavior.py           # Base behavior class
│   ├── farming_behavior.py        # Farming-specific logic
│   └── emergency_behavior.py      # Emergency responses
├── patterns/                       # Reusable pattern library
│   └── pattern_engine.py          # Pattern execution engine
├── events/                         # Event handlers (future)
├── config/                         # Configuration management (future)
└── legacy/                         # Preserve working code
    ├── baritone_path_client.py    # Current working script
    └── *.yml                      # Current pattern files
```

## Key Components

### 1. Base Behavior (`behaviors/base_behavior.py`)

All behaviors inherit from `BaseBehavior`, which provides:
- Lifecycle management (start, execute, cleanup)
- State tracking (idle, running, paused, completed, failed, suspended)
- Priority system (1-10, lower = higher priority)
- Interruption handling

### 2. Pattern Engine (`patterns/pattern_engine.py`)

Executes reusable patterns of movements and actions:
- Movement steps: `"~ ~ ~2"` (relative coordinates)
- Dwell steps: `{"type": "dwell", "period": "3s"}`
- Action steps: `{"type": "action", "action": "harvest"}`
- Condition steps: `{"type": "condition", "check": "inventory_full"}`

### 3. Behavior Engine (`core/behavior_engine.py`)

Orchestrates multiple behaviors:
- Manages behavior queue with priority ordering
- Handles interruptions and emergency situations
- Provides shared context between behaviors
- Runs behaviors in separate threads

### 4. Farming Behavior (`behaviors/farming_behavior.py`)

Handles automated farming:
- Navigates to waypoints
- Executes farming patterns
- Manages farming tools and inventory
- Integrates with pattern engine

### 5. Emergency Behavior (`behaviors/emergency_behavior.py`)

High-priority behavior for urgent situations:
- Pillager attack responses
- Player detection handling
- Low health situations
- Automatic escape to safe locations

## Usage Examples

### Basic Farming Bot

```python
from core.modular_bot_client import ModularBotClient

# Create bot with configuration
client = ModularBotClient("config.yml")

# Start the bot
client.start()

# Bot will automatically:
# 1. Connect to MQTT
# 2. Queue farming behavior
# 3. Execute waypoints and patterns
# 4. Handle emergencies automatically
```

### Adding Custom Behavior

```python
from behaviors.base_behavior import BaseBehavior, BehaviorState

class MiningBehavior(BaseBehavior):
    def can_start(self, context):
        return context.get("mining_enabled", False)
    
    def execute(self, context):
        # Mining logic here
        return True
    
    def cleanup(self, context):
        # Cleanup logic here
        pass

# Add to behavior engine
behavior_engine.add_behavior(MiningBehavior("mining"))
```

### Custom Pattern with Dwell

```yaml
patterns:
  my_custom_pattern:
    - "~ ~ ~2"
    - "~ ~ ~-1"
    - type: dwell
      period: 3s
    - "~ ~ ~2"
    - type: action
      action: harvest
```

## Benefits

### 1. Modularity
- Each behavior has a single responsibility
- Easy to add/remove behaviors
- Patterns are reusable across behaviors

### 2. Emergency Handling
- Automatic interruption of low-priority behaviors
- Dedicated emergency response system
- Configurable safe locations and responses

### 3. Extensibility
- Easy to add new behaviors (mining, building, etc.)
- Pattern system supports complex sequences
- Event system for game event handling

### 4. Maintainability
- Clear separation of concerns
- Easy to test individual components
- Preserved working code in legacy/

### 5. Configuration
- YAML-based configuration
- Behavior-specific settings
- Easy to modify without code changes

## Migration from Legacy

The original working code is preserved in `scripts/legacy/` and continues to work exactly as before. The modular system is an addition, not a replacement.

To migrate:
1. Copy your working patterns to the new config format
2. Test with the modular client
3. Gradually add new behaviors as needed

## Future Enhancements

### Planned Features
- **Inventory Management**: Automatic tool switching, item management
- **Event System**: Game event detection and handling
- **Configuration Management**: Dynamic config reloading
- **Mining Behavior**: Automated mining with pathfinding
- **Building Behavior**: Automated construction
- **Trading Behavior**: Villager trading automation

### Extensibility Points
- Custom behavior types
- Custom pattern step types
- Custom event handlers
- Custom configuration loaders

## Testing

Run the demonstration script to see the architecture in action:

```bash
cd scripts
python3 demo_modular_architecture.py
```

This will show:
- Pattern engine with dwell functionality
- Emergency behavior handling
- Behavior engine orchestration

## Configuration

See `example_modular_config.yml` for a complete configuration example that includes:
- Behavior definitions
- Pattern definitions with dwell
- Emergency response settings
- Service configurations

The modular architecture provides a solid foundation for building complex, maintainable bot behaviors while preserving the simplicity and reliability of the original system.
