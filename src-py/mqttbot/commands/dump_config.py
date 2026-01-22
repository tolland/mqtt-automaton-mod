import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint

from mqttbot.core.modular_bot_client import ModularBotClient

app = typer.Typer(name="config", no_args_is_help=True)

def _get_client(ctx: typer.Context) -> ModularBotClient:
    config = ctx.obj["config"]
    settings = ctx.obj["settings"]
    client = ModularBotClient(settings, str(config))
    client.configure()
    return client


@app.command("all")
def dump_all(
    ctx: typer.Context,
):
    """
    Dump all configuration elements.
    """
    console = Console()
    try:
        client = _get_client(ctx)

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

        rprint("[bold blue]Patterns Config:[/bold blue]")
        pprint(client.patterns_configs)

        rprint("[bold blue]Thread Configs:[/bold blue]")
        for thread_config in client.thread_configs:
            pprint(thread_config)

        rprint("[bold blue]Threads:[/bold blue]")
        for thread in client.threads:
            pprint(thread)

        return 0

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise


@app.command("patterns")
def dump_patterns(
    ctx: typer.Context,
):
    """
    Dump patterns configuration.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        pprint(client.patterns_configs)
        return 0
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@app.command("thread-configs")
def dump_thread_configs(
    ctx: typer.Context,
):
    """
    Dump thread configurations.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        for thread_config in client.thread_configs:
            pprint(thread_config)
        return 0
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@app.command("threads")
def dump_threads(
    ctx: typer.Context,
):
    """
    Dump instantiated threads.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        for thread in client.threads:
            pprint(thread)
        return 0
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@app.command("dump")
def dump_config(
    ctx: typer.Context,
):
    """
    Parse and display the bot configuration without running the bot. (Alias for 'all')
    """
    return dump_all(ctx)
