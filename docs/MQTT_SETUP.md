# MQTT Bot Setup Guide

## Overview
This guide explains how to set up and use the Minecraft MQTT bot with the Python path client.

## Bot Player Name Configuration

### Problem
By default, `./gradlew runClient` generates random player names like "Player123" on each launch, making it difficult to configure the Python client.

### Solution
We've configured a static player name in `build.gradle`:

```gradle
runClient {
    args "--username", "SandyFire"
}
```

### Usage Options

1. **Use default name**: `./gradlew runClient` (uses "SandyFire")
2. **Use custom name**: `./gradlew runClient --args="--username YourBotName"`
3. **Use helper script**: `./run_bot.sh YourBotName`

## MQTT Topic Structure

### Commands (Python → Bot)
- **Catch-all**: `mqttbot/bots/command` (all bots listen)
- **Specific**: `mqttbot/{playerName}/command` (specific bot)

### Replies (Bot → Python)
- **Always**: `mqttbot/{actualPlayerName}/reply` (uses actual player name)

### Position Updates
- **Always**: `mqttbot/{actualPlayerName}/pos` (periodic position updates)

## Python Client Configuration

### Basic Configuration (`scripts/example_config.yml`)

```yaml
# Send commands to all bots
client_id: "bots"

# Expect replies from specific bot (must match actual player name)
expected_player_name: "SandyFire"

# Waypoints using structured JSON
waypoints:
  - x: 100    # Uses {"service": "baritone", "method": "goto", "params": {"x": 100, "y": 64, "z": 200}}
    y: 64
    z: 200
  - name: "home"  # Uses {"service": "baritone", "method": "chat", "params": {"message": "#wp goto home"}}
```

### Alternative Configuration (Direct Bot Communication)

```yaml
# Send commands directly to specific bot
client_id: "SandyFire"

# Expect replies from same bot
expected_player_name: "SandyFire"  # Can be omitted (defaults to client_id)
```

## Message Format

### Goto Command (XYZ Coordinates)
```json
{
  "service": "baritone",
  "method": "goto",
  "requestId": "uuid-here",
  "params": {
    "x": 100,
    "y": 64,
    "z": 200
  },
  "identity": "python_client"
}
```

### Chat Command (Named Waypoints - Legacy)
```json
{
  "service": "baritone", 
  "method": "chat",
  "requestId": "uuid-here",
  "params": {
    "message": "#wp goto home"
  },
  "identity": "python_client"
}
```

### Reply Format (New Structured Response)
```json
{
  "service": "baritone",
  "method": "pathing",
  "requestId": "uuid-here",
  "identity": "mqttbot",
  "response": {
    "type": "CALC_FINISHED_NOW_EXECUTING",
    "player": "SandyFire",
    "goalX": 100,
    "goalY": 64,
    "goalZ": 200,
    "goalType": "GoalBlock"
  }
}
```

### Arrival Reply Format
```json
{
  "service": "baritone",
  "method": "arrived",
  "requestId": "uuid-here",
  "identity": "mqttbot",
  "response": {
    "status": "reached",
    "x": 336,
    "y": 64,
    "z": -2422,
    "detail": "found in tick handler",
    "player": "SandyFire"
  }
}
```

## Running the System

### 1. Start the Bot
```bash
# Option 1: Use default name "SandyFire"
./gradlew runClient

# Option 2: Use custom name
./gradlew runClient --args="--username MyBot"

# Option 3: Use helper script
./run_bot.sh MyBot
```

### 2. Configure Python Client
Update `scripts/example_config.yml`:
- Set `expected_player_name` to match your bot's actual player name
- Use `client_id: "bots"` for catch-all commands

### 3. Run Python Client
```bash
cd scripts
python3 baritone_path_client.py example_config.yml --broker your.mqtt.broker.ip
```

## Troubleshooting

### Issue: "subscribing mqttbot/bots/reply"
**Problem**: Python client subscribes to wrong reply topic  
**Solution**: Set `expected_player_name` in YAML config to actual bot player name

### Issue: Bot not responding to commands
**Problem**: Player name mismatch  
**Solution**: Ensure `expected_player_name` matches the bot's actual username in Minecraft

### Issue: Random player names
**Problem**: `runClient` generates random names  
**Solution**: Use `./gradlew runClient --args="--username StaticName"`

### Issue: Invalid message format
**Problem**: Bot receives non-structured messages  
**Solution**: Ensure all messages use the new MessageData JSON format with `response` field

## Architecture

```
Python Client                    MQTT Broker                     Minecraft Bot
     |                               |                               |
     |---> mqttbot/bots/command ---->|---> mqttbot/bots/command ---->|
     |                               |                               |
     |<--- mqttbot/SandyFire/reply <---|<--- mqttbot/SandyFire/reply <---|
     |                               |                               |
     |<--- mqttbot/SandyFire/pos <-----|<--- mqttbot/SandyFire/pos <-----|
```

## Event-Driven Automation

The system now supports automated responses to game events through configurable event handlers.

### Event Configuration

Add event handlers to your YAML config:

```yaml
events:
  night_start:
    enabled: true
    steps:
      - service: baritone
        method: pause
        description: "Pause current pathing"
      - service: warp
        method: teleport
        params:
          message: "warp home"
          radius: 5
          target:
            x: 0
            y: 64
            z: 0
        description: "Warp to home base"
      - service: sleep
        method: start
        description: "Start sleeping"
        
  day_start:
    enabled: true
    steps:
      - service: baritone
        method: resume
        description: "Resume pathing after sleep"
```

### Supported Events

- **night_start**: Triggered when night begins
- **day_start**: Triggered when day begins  
- **on_damage**: Triggered when bot takes damage (future)

### Command Types and Completion

Commands are classified into two types:

#### 1. No-Reply Commands
- Execute immediately without waiting for completion
- Examples: `baritone.pause`, `baritone.resume`, `commands.chatMessage`

#### 2. Reply-Expected Commands  
- Wait for standard success/failure response
- Configurable timeout per service
- Examples: `baritone.goto`, `sleep.start`, `warp.teleport`

#### Service Configuration
```yaml
services:
  baritone:
    commands:
      pause:
        type: "no-reply"
      goto:
        type: "reply-expected"
        timeout: 60
  sleep:
    commands:
      start:
        type: "reply-expected"
        timeout: 30
  warp:
    commands:
      teleport:
        type: "reply-expected"
        timeout: 15
        command_template: "warp {name}"  # Default template, can be overridden per-event
```

#### Standard Response Format

**Success Response:**
```json
{
  "service": "baritone",
  "method": "goto",
  "response": {
    "status": "success",
    "message": "Goal reached",
    "x": 100, "y": 64, "z": 200,
    "player": "SandyFire"
  }
}
```

**Failure Response:**
```json
{
  "service": "sleep", 
  "method": "start",
  "response": {
    "status": "failure",
    "message": "Sleep failed",
    "reason": "No bed found nearby",
    "player": "SandyFire"
  }
}
```

**Warp Success Response:**
```json
{
  "service": "warp",
  "method": "teleport", 
  "response": {
    "status": "success",
    "message": "Warp completed - arrived at home",
    "player": "SandyFire",
    "warpName": "home",
    "targetX": 0, "targetY": 64, "targetZ": 0,
    "x": 1.2, "y": 64.0, "z": -0.8
  }
}
```

#### Warp Command Templates

The warp service supports different server plugins by using configurable command templates:

**Common Server Plugin Examples:**
```yaml
# Vanilla/Basic warp plugins
command_template: "warp {name}"           # → warp home

# Essentials plugin  
command_template: "home {name}"           # → home home
command_template: "warp {name}"           # → warp spawn

# HuskHomes plugin
command_template: "home tp {name}"        # → home tp home

# Custom plugins with slash commands
command_template: "/warp {name}"          # → /warp home
command_template: "/home {name}"          # → /home home
```

**Per-Event Template Override:**
```yaml
events:
  night_start:
    steps:
      - service: warp
        method: teleport
        params:
          name: "home"
          command_template: "home tp {name}"  # Override default template
          radius: 5
          target: {x: 345, y: 64, z: -2943}
```

### Event Message Format

Events are sent as structured messages:

#### Lifecycle Events

The system supports lifecycle events that are triggered automatically during waypoint processing:

- **`waypoints_start`**: Triggered at the beginning of all waypoint processing
- **`waypoint_start`**: Triggered before each individual waypoint (safe travel)
- **`pattern_start`**: Triggered before pattern execution (enable farming)
- **`pattern_end`**: Triggered after pattern execution (disable farming)
- **`waypoint_end`**: Triggered after each waypoint and its patterns complete
- **`waypoints_end`**: Triggered after all waypoints are completed

Lifecycle events run in parallel with waypoint processing and do not interrupt the main flow.

```json
{
  "service": "events",
  "method": "time_change", 
  "response": {
    "event": "night_start",
    "message": "Night has started",
    "player": "SandyFire",
    "timestamp": 1640995200000
  }
}
```

## Next Steps

1. **Direct Baritone API**: Replace chat commands with direct Baritone API calls
2. **Waypoint Resolution**: Implement coordinate lookup for named waypoints
3. **Error Handling**: Add better error responses and retry logic
4. **Multiple Bots**: Support coordinating multiple bots simultaneously
5. **Advanced Events**: Add damage, inventory, and custom trigger events
