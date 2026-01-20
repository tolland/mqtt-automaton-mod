import sys

import typer
from rich import print as rprint, inspect
from rich.console import Console
from rich.panel import Panel

from mqttbot.core.modular_bot_client import ModularBotClient

app = typer.Typer(name="config", no_args_is_help=True)

@app.command("dump")
def dump_config(
        ctx: typer.Context,
):
    """
    Parse and display the bot configuration without running the bot.

    This command loads the configuration file, parses threads and patterns,
    and displays the parsed configuration in a readable format.
    """
    console = Console()
    try:
        config = ctx.obj["config"]
        settings = ctx.obj["settings"]
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

        for thread in client.threads:
            inspect(thread)

        return 0

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise
