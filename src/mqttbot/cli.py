"""Command-line interface for MQTT bot."""

import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from mqttbot.client import PathingClient
from mqttbot.config import build_settings

app = typer.Typer(
    name="mqttbot",
    help="MQTT-based Minecraft bot automation with Baritone integration",
    add_completion=False,
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
):
    """
    Run the MQTT bot with the specified configuration.

    The configuration file should contain waypoints, patterns, and service definitions.
    See the documentation for YAML format details.
    """
    try:
        # Build settings from config and CLI args
        settings, waypoints, patterns = build_settings(
            config_path=config,
            broker=broker,
            port=port,
            client_id=client_id,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )

        # Display startup info
        rprint(
            Panel.fit(
                f"[bold cyan]MQTT Bot Starting[/bold cyan]\n"
                f"Config: [yellow]{config}[/yellow]\n"
                f"Broker: [green]{settings.broker}:{settings.port}[/green]\n"
                f"Client ID: [blue]{settings.client_id}[/blue]\n"
                f"Waypoints: [magenta]{len(waypoints)}[/magenta]",
                title="🤖 mqttbot",
                border_style="cyan",
            )
        )

        # Create and run client
        client = PathingClient(settings, waypoints, patterns)
        try:
            client.connect()
            rc = client.run()
            sys.exit(rc)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
            sys.exit(130)
        finally:
            client.close()

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise


@app.command()
def version():
    """Show version information."""
    from mqttbot import __version__

    rprint(f"[bold cyan]mqttbot[/bold cyan] version [green]{__version__}[/green]")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
