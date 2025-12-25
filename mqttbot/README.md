# mqttbot

Python package for controlling Minecraft bots via MQTT with Baritone integration.

## Installation

### Using uv (recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Usage

```bash
mqttbot run config.yaml --broker 127.0.0.1 --port 1883
```

### CLI Options

- `config`: Path to YAML configuration file (required)
- `--broker`, `-b`: MQTT broker hostname (default: 127.0.0.1)
- `--port`, `-p`: MQTT broker port (default: 1883)
- `--client-id`, `-c`: Client ID (overrides config file)
- `--timeout`, `-t`: Timeout in seconds per waypoint
- `--retries`, `-r`: Maximum number of retries
- `--retry-delay`, `-d`: Delay in seconds between retries

## Configuration

See the main project README for YAML configuration format.

## Development

Install with development dependencies:

```bash
uv pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
black mqttbot/
ruff check mqttbot/
```

## Package Structure

```
mqttbot/
├── __init__.py       # Package initialization
├── models.py         # Data models (MessageData, Settings)
├── config.py         # Configuration loading
├── client.py         # PathingClient - core bot logic
└── cli.py            # Typer-based CLI interface
```

## Migration from baritone_path_client.py

The old `scripts/baritone_path_client.py` script is now deprecated.
Use `mqttbot` command instead:

**Old:**
```bash
python scripts/baritone_path_client.py config.yaml --broker 127.0.0.1
```

**New:**
```bash
mqttbot run config.yaml --broker 127.0.0.1
```

All functionality is preserved, with improved:
- Type hints and modern Python 3.10+ syntax
- Modular package structure
- Rich console output with colors
- Better error handling
