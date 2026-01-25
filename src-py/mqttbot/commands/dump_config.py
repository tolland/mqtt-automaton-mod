import traceback

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint

from mqttbot.config.model.full_config import FullConfig
from mqttbot.core.modular_bot_client import ModularBotClient
from mqttbot.utils.loader import _load_config

app = typer.Typer(
    name="config",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _get_client(ctx: typer.Context) -> ModularBotClient:
    config = ctx.obj["config"]
    settings = ctx.obj["settings"]
    client = ModularBotClient(settings, str(config))
    client.configure()
    return client


def _handle_error(console: Console, error: Exception, debug: bool) -> int:
    """Handle errors with optional verbose output."""
    if debug:
        # debug_console = Console()
        # debug_console.print_exception(show_locals=True)
        traceback.print_exc()
        return 1
    else:
        console.print(f"[red]❌ Error: {error}[/red]")
        return 1


@app.command("all")
def dump_all(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
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
                f"",
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
        return _handle_error(console, e, debug)


@app.command("patterns")
def dump_patterns(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Dump patterns configuration.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        rprint(client.patterns_configs)
        return 0
    except Exception as e:
        return _handle_error(console, e, debug)


@app.command("thread-configs")
def dump_thread_configs(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
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
        return _handle_error(console, e, debug)


@app.command("threads")
def dump_threads(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Dump instantiated threads.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        for thread in client.threads:
            rprint(thread)
            pprint(thread)
            # inspect(thread)
        return 0
    except Exception as e:
        return _handle_error(console, e, debug)



@app.command("event-handlers")
def dump_event_handlers(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Dump instantiated threads.
    """
    console = Console()
    try:
        client = _get_client(ctx)
        rprint(client.event_manager.handlers)
        return 0
    except Exception as e:
        return _handle_error(console, e, debug)


@app.command("dump")
def dump_config(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Parse and display the bot configuration without running the bot. (Alias for 'all')
    """
    return dump_all(ctx, debug=debug)


@app.command("pydantic")
def parse_config_pydantic(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Parse config using visitor pattern to validate structure.
    """
    config = ctx.obj["config"]

    config_yaml = _load_config(config)
    model = FullConfig.model_validate(config_yaml)
    rprint(model.patterns)

@app.command("pydantic-threads")
def parse_threads_pydantic(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Parse config using visitor pattern to validate structure.
    """
    config = ctx.obj["config"]

    config_yaml = _load_config(config)
    model = FullConfig.model_validate(config_yaml)
    rprint(model)


@app.command("pydantic-events")
def parse_threads_pydantic(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Parse config using visitor pattern to validate structure.
    """
    config = ctx.obj["config"]

    config_yaml = _load_config(config)
    model = FullConfig.model_validate(config_yaml)
    rprint(model.event_handlers)


@app.command("pydantic-patterns")
def parse_patterns_pydantic(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Show full error details"),
):
    """
    Parse config using visitor pattern to validate structure.
    """
    config = ctx.obj["config"]

    config_yaml = _load_config(config)
    model = FullConfig.model_validate(config_yaml)
    rprint(model.pattern_config)
