import asyncio
import atexit
import signal
import sys

import typer
from rich import print as rprint
from rich.panel import Panel

from mqttbot.config.config import build_settings


app = typer.Typer(name="dump_config", no_args_is_help=True)

@app.command()
def dump_config(

):
    """
    Parse and display the bot configuration without running the bot.

    This command loads the configuration file, parses threads and patterns,
    and displays the parsed configuration in a readable format.
    """
    try:
        # Build settings from config and CLI args
        settings = build_settings(
            config_path=config,
            broker=broker,
            port=port,
            client_id=client_id,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
            log_level=log_level,
        )

        # Display startup info
        rprint(
            Panel.fit(
                f"[bold cyan]MQTT Bot Config Dump[/bold cyan]\n"
                f"Config: [yellow]{config}[/yellow]\n"
                f"Broker: [green]{settings.broker}:{settings.port}[/green]\n"
                f"Client ID: [blue]{settings.client_id}[/blue]\n",
                title="📋 Config Parser",
                border_style="cyan",
            )
        )

        # Create client (loads config and initializes components)
        client = ModularBotClient(settings, str(config))

        # Parse config by calling start() (but don't actually run)
        client.configure()

        # Display summary
        rprint(
            Panel.fit(
                f"[green]✓[/green] Configuration parsed successfully\n"
                f"Threads: [cyan]{len(client._scheduler._threads) if hasattr(client._scheduler, '_threads') else 'N/A'}[/cyan]\n"
                f"Event handlers: [cyan]{len(client.event_manager.handlers)}[/cyan]",
                title="✅ Parse Complete",
                border_style="green",
            )
        )

        return 0

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise
