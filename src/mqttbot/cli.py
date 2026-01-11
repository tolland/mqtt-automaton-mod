"""Command-line interface for MQTT bot."""
import asyncio
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from mqttbot.config.config import build_settings
from mqttbot.modular_bot_client import ModularBotClient

app = typer.Typer(
    name="mqttbot",
    help="MQTT-based Minecraft bot automation with Baritone integration",
    add_completion=False,
    pretty_exceptions_enable=False,
)
console = Console()


@app.command()
def run(
        config: Path = typer.Argument(
            ...,
            help="Path to config/waypoints YAML file",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
        broker: str = typer.Option(
            "127.0.0.1",
            "--broker",
            "-b",
            help="MQTT broker hostname or IP",
        ),
        port: int = typer.Option(
            1883,
            "--port",
            "-p",
            help="MQTT broker port",
        ),
        client_id: str = typer.Option(
            None,
            "--client-id",
            "-c",
            help="Client ID (overrides config file)",
        ),
        timeout: int = typer.Option(
            None,
            "--timeout",
            "-t",
            help="Timeout in seconds per waypoint",
        ),
        retries: int = typer.Option(
            None,
            "--retries",
            "-r",
            help="Maximum number of retries",
        ),
        retry_delay: int = typer.Option(
            None,
            "--retry-delay",
            "-d",
            help="Delay in seconds between retries",
        ),
        log_level: str = typer.Option(
            None,
            "--log-level",
            "-l",
            help="override log level (DEBUG, INFO, WARNING, ERROR)",
        ),
):
    """
    Run the MQTT bot with the specified configuration.

    The configuration file should contain waypoints, patterns, and service definitions.
    See the documentation for YAML format details.
    """
    try:
        # Build settings from config and CLI args
        # Note: waypoints and patterns are now parsed by ModularBotClient from config
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
                f"[bold cyan]MQTT Bot Starting[/bold cyan]\n"
                f"Config: [yellow]{config}[/yellow]\n"
                f"Broker: [green]{settings.broker}:{settings.port}[/green]\n"
                f"Client ID: [blue]{settings.client_id}[/blue]\n",
                title="🤖 mqttbot",
                border_style="cyan",
            )
        )

        # Create and run modular bot client
        client = ModularBotClient(settings, str(config))
        rc = asyncio.run(client.run())
        sys.exit(rc)

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(2)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise


@app.command()
def version() -> None:
    """Show version information."""
    from mqttbot import __version__

    rprint(f"[bold cyan]mqttbot[/bold cyan] version [green]{__version__}[/green]")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
