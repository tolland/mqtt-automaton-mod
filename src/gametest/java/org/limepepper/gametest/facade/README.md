# Test Server Facade

This package provides a unified interface for testing against both integrated servers (singleplayer) and external servers (PaperMC/Spigot).

## Overview

The facade pattern allows tests to work seamlessly with:
- **Integrated servers**: Direct JVM access via `TestSingleplayerContext`
- **External servers**: Remote PaperMC/Spigot instances via client commands

## Key Components

### TestServerFacade (Interface)
```java
public interface TestServerFacade {
    void executeCommand(String command);
    TestClientWorldContext getClientWorld();
    boolean isIntegratedServer();
    String getPlayerName();
}
```

### IntegratedServerFacade
Wraps `TestSingleplayerContext` for direct server access:
- Commands execute synchronously on the server thread
- Full validation and error reporting
- Uses `@p` selector for player targeting

### ExternalServerFacade
Wraps `ExternalServerConnection` for remote servers:
- Commands sent via chat as OP player
- 2-tick delay for server processing
- Uses actual player name from connection

## Usage Examples

### Example 1: Integrated Server (Singleplayer)
```java
@Override
public void runTest(ClientGameTestContext context) {
    TestWorldBuilder worldBuilder = context.worldBuilder();

    try (TestSingleplayerContext spContext = worldBuilder.create()) {
        // Create facade
        TestServerFacade server = new IntegratedServerFacade(spContext);

        // Use facade with MiniTestContext
        try (MiniTestContext testCtx = new MiniTestContext(context, server)) {
            testCtx.setBlock(0, 0, 0, "minecraft:stone");
            testCtx.teleportPlayer(5, 0, 5, 0, 0);

            // Or use directly
            server.executeCommand("time set noon");
            server.getClientWorld().waitForChunksRender();
        }
    }
}
```

### Example 2: External Server (PaperMC)
```java
@Override
public void runTest(ClientGameTestContext context) {
    // Connect to external PaperMC server
    try (ExternalServerConnection conn =
            ExternalServerContext.connect(context, "docker.lan", 25565, "Mqtt-bot")) {

        // Create facade
        TestServerFacade server = new ExternalServerFacade(context, conn, "Mqtt-bot");

        // Use same code as integrated server!
        try (MiniTestContext testCtx = new MiniTestContext(context, server)) {
            testCtx.setBlock(0, 0, 0, "minecraft:stone");
            testCtx.teleportPlayer(5, 0, 5, 0, 0);

            server.executeCommand("time set noon");
            server.getClientWorld().waitForChunksRender();
        }
    }
}
```

### Example 3: Portable Tests
Write tests that work with both server types:

```java
private void runPortableTest(ClientGameTestContext context, TestServerFacade server) {
    // Setup
    server.executeCommand("time set noon");
    server.executeCommand("weather clear");

    try (MiniTestContext testCtx = new MiniTestContext(context, server)) {
        // Place test blocks
        Map<String, String> blocks = MiniTestContext.createCommonBlockDict();
        testCtx.setBlockLayer(-1, blocks, new String[][]{
            {"stone", "stone", "stone"},
            {"stone", "player", "stone"},
            {"stone", "stone", "stone"}
        });

        // Wait for chunks
        server.getClientWorld().waitForChunksRender();

        // Run test logic...
        testCtx.teleportPlayer(0, 0, 0, 0, 0);

        // Test automatically cleans up on close
    }
}

// Use with integrated server
try (TestSingleplayerContext sp = worldBuilder.create()) {
    runPortableTest(context, new IntegratedServerFacade(sp));
}

// Or use with external server
try (ExternalServerConnection conn = ExternalServerContext.connect(...)) {
    runPortableTest(context, new ExternalServerFacade(context, conn, "Mqtt-bot"));
}
```

## Behavior Differences

| Operation | Integrated Server | External Server |
|-----------|------------------|-----------------|
| Command execution | Direct server-side | Via chat (OP player) |
| Command validation | Pre-validated | No validation |
| Return values | Available | Not available |
| Synchronous | Yes | No (2-tick delay) |
| Player targeting | `@p` selector | Actual player name |

## Migration Guide

### Old Code (TestServerContext)
```java
public void oldTest(ClientGameTestContext context, TestServerContext server) {
    BotTestHelper.runCommand(server, "time set noon");
    BotTestHelper.clearNearbyItems(server);
}
```

### New Code (TestServerFacade)
```java
public void newTest(ClientGameTestContext context, TestServerFacade server) {
    server.executeCommand("time set noon");
    server.executeCommand("kill @e[type=item]");
    // Or still use BotTestHelper - it supports both!
    BotTestHelper.runCommand(server, "time set noon");
    BotTestHelper.clearNearbyItems(server);
}
```

## Benefits

1. **Write once, test everywhere**: Same test code works on both integrated and external servers
2. **Flexible testing**: Test client-side Fabric mods against real PaperMC plugins
3. **Gradual migration**: BotTestHelper supports both old and new APIs
4. **Consistent semantics**: Commands work the same regardless of server type
5. **Isolated test areas**: MiniTestContext provides automatic setup/cleanup
