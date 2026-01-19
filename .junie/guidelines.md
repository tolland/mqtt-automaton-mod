# Mqttbot control system for minecraft fabric based mod
    
This document outlines the coding standards, architectural patterns, and best practices for developing this project.

## Technology stack

### Frontend client

The mqttbot client is a python command line application using typer library and the paho mqtt client. The mqttbot client implements a priority-based task scheduling system. The mqttbot client is using pytest for testing. We are using uv for virtual environment management. The python package source is located at src-py , the package configuration file is pyproject.toml

### Backend

The mqttmod mod is a java fabric mod that runs in the Minecraft game client. It uses the fabric-loom gradle plugin for building. The mod listens for mqtt messages and implements the requests using various backend integrations. We are using the fabric-gametest api to implement single player and integrated server tests. The source is located under src/main the gametest implementation is under "src/gametest". We have normal junit tests under src/test for unit tests

## Details

### backend Integrations

For movement and pathing operations, we are using the baritone api. The baritone library supports pathing, e.g. goto x,y,z, and other composite operations such as farming, and mining. The mod implements a wrapper around baritone calls to implement detection of state transitions such as pathing, goal reached, timeout. We are also using the wurst mod as an integration that provides interactions capabilities such as autofarm (farms nearby blocks) and autoshopgui (which performs a trade interaction with a npc merchant)

## Changes to code

After making changes to java code:

./gradlew spotlessCheck build

To fix formatting errors:

./gradlew spotlessApply

## Testing

* `uv run pytest`
* `./gradlew test`
