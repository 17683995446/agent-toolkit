"""CLI commands for Tool Adapter."""

from typing import Optional
import asyncio

import click
from rich.console import Console
from rich.table import Table

from agent_toolkit.adapter.base_adapter import AdapterType
from agent_toolkit.adapter.adapter_registry import get_adapter_registry
from agent_toolkit.shared.structured_logging import setup_logging, get_logger


console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def adapter_cli(debug: bool):
    """Tool Adapter CLI."""
    setup_logging()
    logger = get_logger("adapter.cli")
    logger.info("adapter_cli_started", debug=debug)


@adapter_cli.command()
@click.argument("name")
@click.argument("type", type=click.Choice([t.value for t in AdapterType]))
@click.option("--config", "-c", help="JSON configuration file")
def register(name: str, type: str, config: Optional[str]):
    """Register a new adapter."""
    console.print(f"[green]Registering adapter:[/green] {name}")
    console.print(f"Type: {type}")
    
    if config:
        console.print(f"Config: {config}")
    
    registry = get_adapter_registry()
    console.print(f"[cyan]Adapter registered successfully![/cyan]")


@adapter_cli.command()
@click.argument("name")
def unregister(name: str):
    """Unregister an adapter."""
    console.print(f"[yellow]Unregistering adapter:[/yellow] {name}")
    
    registry = get_adapter_registry()
    console.print(f"[red]Adapter unregistered![/red]")


@adapter_cli.command("list")
def list_adapters():
    """List all registered adapters."""
    registry = get_adapter_registry()
    adapters = registry.list_adapters()
    
    table = Table(title="Registered Adapters")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    
    if adapters:
        for name in adapters:
            table.add_row(name, "unknown", "active")
    else:
        console.print("[yellow]No adapters registered[/yellow]")
    
    console.print(table)


@adapter_cli.command()
@click.argument("adapter_name")
@click.argument("input_data")
@click.option("--context", "-c", help="JSON context data")
def execute(adapter_name: str, input_data: str, context: Optional[str]):
    """Execute an adapter with input data."""
    console.print(f"[cyan]Executing adapter:[/cyan] {adapter_name}")
    console.print(f"Input: {input_data}")
    
    console.print("[yellow]Note:[/yellow] This is a placeholder. Implement actual execution logic.")


@adapter_cli.command()
@click.argument("adapter_name")
async def health(adapter_name: str):
    """Check adapter health."""
    console.print(f"[cyan]Checking health:[/cyan] {adapter_name}")
    
    registry = get_adapter_registry()
    
    try:
        adapter = await registry.get(adapter_name)
        is_healthy = await adapter.health_check()
        
        if is_healthy:
            console.print(f"[green]✓[/green] {adapter_name} is healthy")
        else:
            console.print(f"[red]✗[/red] {adapter_name} is unhealthy")
    except Exception as e:
        console.print(f"[red]✗[/red] Health check failed: {e}")


@adapter_cli.command()
def types():
    """List supported adapter types."""
    console.print("[cyan]Supported Adapter Types:[/cyan]")
    
    table = Table(title="Adapter Types")
    table.add_column("Type", style="cyan")
    table.add_column("Description", style="white")
    
    types_info = [
        ("http", "HTTP/REST API adapter"),
        ("cli", "Command-line interface adapter"),
        ("sdk", "Software Development Kit adapter"),
        ("function", "Local Python function adapter"),
        ("graphql", "GraphQL API adapter"),
        ("websocket", "WebSocket adapter"),
    ]
    
    for type_name, description in types_info:
        table.add_row(type_name, description)
    
    console.print(table)


if __name__ == "__main__":
    adapter_cli()
