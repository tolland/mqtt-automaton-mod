import asyncio
import atexit
import signal
import sys

import typer
from rich.console import Console

from mqttbot.core.modular_bot_client import ModularBotClient

app = typer.Typer(name="run")


@app.callback()
def run_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo("in the query callback")


@app.command("run-command")
def run_command(
        ctx: typer.Context,
):
    """
    Run the MQTT bot with the specified configuration.

    The configuration file should contain waypoints, patterns, and service definitions.
    See the documentation for YAML format details.
    """
    console = Console()

    try:

        config = ctx.obj["config"]
        settings = ctx.obj["settings"]
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
