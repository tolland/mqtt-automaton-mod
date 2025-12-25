# MqttBot Logging System

## Overview

The MqttBot now uses a proper logging system based on SLF4J (which Fabric provides by default) instead of `System.out.println()` statements. This provides better control over log output and performance.

## Configuration

The logging system is controlled by a YAML configuration file named `config.yml` in the project root.

### Log Levels

Available log levels (from most verbose to least):
- `TRACE` - Most detailed logging
- `DEBUG` - Debug information (includes event and MQTT debugging)  
- `INFO` - General information (default)
- `WARN` - Warnings only
- `ERROR` - Errors only

### Configuration File Structure

```yaml
# Log levels: TRACE, DEBUG, INFO, WARN, ERROR
log_level: DEBUG

# MQTT Configuration
mqtt:
  broker: "tcp://mosquitto.lan:1883"
  qos: 2
  
# Bot Configuration  
bot:
  # Enable/disable specific debug categories
  debug_events: true
  debug_mqtt: true
```

### Debug Categories

The system provides specific debug categories:
- `debug_events`: Controls detailed event system logging
- `debug_mqtt`: Controls detailed MQTT communication logging

These categories only work when `log_level` is set to `DEBUG` or `TRACE`.

## Usage Examples

### Quiet Operation (minimal logging)
Copy `config-example-quiet.yml` to `config.yml` for minimal log output:
```yaml
log_level: WARN
bot:
  debug_events: false
  debug_mqtt: false
```

### Debug Mode (verbose logging)
Copy `config-example-debug.yml` to `config.yml` for detailed logging:
```yaml
log_level: DEBUG
bot:
  debug_events: true
  debug_mqtt: true
```

## Implementation Details

### Key Classes

1. **MqttBotConfig** - Loads and manages configuration from `config.yml`
2. **MqttBotLogger** - Wrapper around SLF4J logger with config-aware logging
3. **Updated Classes** - All major classes now use proper logging:
   - EventManager
   - MqttClientInternal
   - MqttBotClientModInitializer

### Logger Usage

The new logging system replaces all `System.out.println()` statements with appropriate log levels:

```java
// Old way
System.out.println("=== DEBUG: Something happened ===");

// New way  
LOGGER.debug("Something happened");
LOGGER.debugEvents("Event-specific debug info");
LOGGER.debugMqtt("MQTT-specific debug info");
```

### Performance Benefits

- Log messages are only processed when the log level allows it
- No string concatenation overhead for disabled log levels
- Proper log formatting and timestamps
- Integration with Fabric's logging infrastructure

## Migration from System.out.println

The following debug output has been converted to proper logging:

- EventManager debug output → `debugEvents()` calls
- MQTT communication debug → `debugMqtt()` calls  
- Error stack traces → `LOGGER.error()` with exception parameter
- General debug info → `LOGGER.debug()` calls
- Warning messages → `LOGGER.warn()` calls

## Testing

To test the logging system:

1. Set `log_level: DEBUG` in `config.yml`
2. Set `debug_events: true` and `debug_mqtt: true`
3. Run the mod and execute `/test_reply` command
4. Check the logs for detailed debug output

To test quiet mode:
1. Set `log_level: WARN` in `config.yml`  
2. Set debug flags to `false`
3. Run the mod - you should see minimal log output
