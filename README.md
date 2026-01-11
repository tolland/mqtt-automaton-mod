# Mqtt automaton mod

This mod was originally designed to allow automating baritone operations to reproduce transient odd behaviour when
building litematica schematics. However, it has
since been extended to support a variety of automations of other modes, based on either
API or direct command calls into them.

## Prerequisites

The automation communicates to the bot using mqtt. Therefore, you need a mqtt server
instance running that both the client and the instance can connect to. I recommend
mosquitto, because it is very simple to setup, however any mqtt server should work.

Currently the mod depends on having baritone and Wurst installed in the client.

## Getting started

Initially you want to check the mod loaded and connected to mqtt:

```
[16:55:12] [main/INFO] (FabricLoader) Loading 56 mods:
	- baritone 1.15.0
	...
	- mqttbot 1.0.1
	...
```

You should also see some logging related to mqtt connectivity:

```
[16:55:25] [Render thread/INFO] (Minecraft) [STDOUT]: Starting MqttBot Client...
[16:55:25] [Render thread/INFO] (MqttClientInternal) Initializing MqttClientInternal
[16:55:25] [Render thread/INFO] (MqttClientInternal) Initializing MQTT client
[16:55:25] [Render thread/INFO] (MqttClientInternal) MQTT ClientId: Player614
[16:55:25] [Render thread/INFO] (MqttClientInternal) Connected to MQTT broker: tcp://mosquitto.lan:1883
[16:55:25] [Render thread/INFO] (MqttClientInternal) Subscribing to MQTT topics: mqttbot/bots/command, mqttbot/Player614/command
[16:55:25] [Render thread/INFO] (MqttClientInternal) MqttClientInternal initialized successfully
```

If that is successful, you can try interacting with the bot via mqtt:

In the simple case you can send a raw json message to the "all bots" topic, which will send the included message to the chat session of the client:

```shell

mosquitto_pub \
  -h mosquitto.lan \
  -t "mqttbot/bots/command" \
  -m '{"service":"commands","method":"chatMessage","params":{"message":"Hello, I am mqttbot"}}'

```

![mqtt chat message example](docs/images/hello_I_am_mqttbot.png "send a message to chat")


```shell

mosquitto_pub \
  -h mosquitto.lan \
  -t "mqttbot/bots/command" \
   -m '{"service":"commands","method":"sendCommand","params":{"message":"time set midnight"}}'

```

![mqtt common example](docs/images/command_time_set_midnight.png "Set the time to midnight using a command")

```mermaid

sequenceDiagram
    participant Main as Main Loop
    participant Sched as Scheduler
    participant CurThread as Current Thread
    participant ReadyQ as Ready Queue
    participant SuspQ as Suspended Stack
    participant Task as Current Task

    Main->>Sched: step()
    
    alt Should Preempt?
        Sched->>ReadyQ: peek highest priority
        alt Higher priority exists
            Sched->>CurThread: suspend()
            CurThread->>Task: suspend()
            Task-->>CurThread: TaskContext
            CurThread-->>Sched: TaskContext
            Sched->>SuspQ: push(CurThread)
            Sched->>ReadyQ: pop()
            Sched->>CurThread: (new) start() or resume()
        end
    end
    
    alt Current thread exists
        Sched->>CurThread: step()
        CurThread->>Task: step()
        Task-->>CurThread: bool (completed?)
        
        alt Task completed
            CurThread->>Task: exit()
            CurThread->>CurThread: _advance_to_next_task()
            
            alt More tasks in queue
                CurThread->>Task: (new) start()
            else Queue empty
                CurThread-->>Sched: return True
                Sched->>SuspQ: peek()
                alt Suspended threads exist
                    Sched->>SuspQ: pop()
                    Sched->>CurThread: (resumed) resume(ctx)
                    CurThread->>Task: resume(ctx)
                else No suspended threads
                    Sched->>CurThread: null (idle)
                end
            end
        else Task continues
            CurThread-->>Sched: return False
        end
    else No current thread
        Sched->>ReadyQ: pop()
        Sched->>CurThread: (new) start()
    end
    
    Sched-->>Main: done

```
