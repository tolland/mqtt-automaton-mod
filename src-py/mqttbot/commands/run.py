import asyncio
import atexit
import signal
import sys

import typer
from rich import print as rprint
from rich.panel import Panel

from mqttbot.config.config import build_settings

app = typer.Typer(name="run", no_args_is_help=True)


@app.callback()
def run_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo(f"in the query callback")


@app.command()
def run_command(

):
    """
    Run the MQTT bot with the specified configuration.

    The configuration file should contain waypoints, patterns, and service definitions.
    See the documentation for YAML format details.
    """

    sys.exit(1)
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

        def cleanup(message: str = ""):
            # print(f"cleaning up requests_debugger: {message}")
            client.exit()

        atexit.register(cleanup, "atexit")
        signal.signal(signal.SIGINT, lambda signum, frame: cleanup("sigint"))
        signal.signal(signal.SIGTERM, lambda signum, frame: cleanup("sigterm"))

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
