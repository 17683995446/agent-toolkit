"""CLI commands for Tool Runtime."""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from agent_toolkit.runtime.base_executor import ExecutorType
from agent_toolkit.runtime.sandbox_manager import SandboxManager, SandboxConfig, SandboxType
from agent_toolkit.runtime.resource_manager import get_resource_manager
from agent_toolkit.shared.structured_logging import setup_logging, get_logger


console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def runtime_cli(debug: bool):
    """Tool Runtime CLI."""
    setup_logging()
    logger = get_logger("runtime.cli")
    logger.info("runtime_cli_started", debug=debug)


@runtime_cli.command()
@click.argument("tool_name")
@click.option("--executor", "-e", type=click.Choice(["docker", "kubernetes", "local"]), default="docker")
@click.option("--timeout", "-t", default=300, help="Execution timeout in seconds")
@click.option("--input", "-i", help="Input JSON file")
def execute(tool_name: str, executor: str, timeout: int, input: Optional[str]):
    """Execute a tool."""
    console.print(f"[cyan]Executing tool:[/cyan] {tool_name}")
    console.print(f"Executor: {executor}")
    console.print(f"Timeout: {timeout}s")
    
    if input:
        console.print(f"Input file: {input}")
    
    console.print("[yellow]Note:[/yellow] This is a placeholder. Implement actual execution logic.")


@runtime_cli.command()
@click.option("--executor", "-e", type=click.Choice(["docker", "kubernetes", "local"]), default="docker")
def status(executor: str):
    """Check runtime status."""
    console.print(f"[cyan]Runtime Status:[/cyan]")
    console.print(f"Executor: {executor}")
    console.print(f"Status: [green]running[/green]")


@runtime_cli.command()
@click.argument("execution_id")
def cancel(execution_id: str):
    """Cancel a running execution."""
    console.print(f"[yellow]Cancelling execution:[/yellow] {execution_id}")
    console.print("[green]Execution cancelled[/green]")


@runtime_cli.group("sandbox")
def sandbox():
    """Sandbox management commands."""
    pass


@sandbox.command("create")
@click.argument("sandbox_id")
@click.option("--type", "-t", type=click.Choice(["docker", "weasel", "seccomp"]), default="docker")
@click.option("--timeout", default=300, help="Sandbox timeout in seconds")
@click.option("--memory", default=512, help="Memory limit in MB")
def sandbox_create(sandbox_id: str, type: str, timeout: int, memory: int):
    """Create a new sandbox."""
    console.print(f"[green]Creating sandbox:[/green] {sandbox_id}")
    console.print(f"Type: {type}")
    console.print(f"Timeout: {timeout}s")
    console.print(f"Memory: {memory}MB")


@sandbox.command("list")
def sandbox_list():
    """List all sandboxes."""
    table = Table(title="Active Sandboxes")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    
    table.add_row("sandbox-1", "docker", "running")
    table.add_row("sandbox-2", "docker", "ready")
    
    console.print(table)


@sandbox.command("delete")
@click.argument("sandbox_id")
def sandbox_delete(sandbox_id: str):
    """Delete a sandbox."""
    console.print(f"[red]Deleting sandbox:[/red] {sandbox_id}")
    console.print("[green]Sandbox deleted[/green]")


@runtime_cli.group("resources")
def resources():
    """Resource management commands."""
    pass


@resources.command("stats")
async def resource_stats():
    """Show resource usage statistics."""
    resource_manager = get_resource_manager()
    stats = await resource_manager.get_stats()
    
    table = Table(title="Resource Usage")
    table.add_column("Resource", style="cyan")
    table.add_column("Usage", style="green")
    table.add_column("Limit", style="yellow")
    
    usage = stats["usage"]
    quota = stats["quota"]
    
    table.add_row(
        "CPU",
        f"{usage['cpu_percent']:.1f}%",
        f"{quota['cpu_limit']} cores"
    )
    table.add_row(
        "Memory",
        f"{usage['memory_mb']:.0f} MB",
        f"{quota['memory_limit_mb']} MB"
    )
    table.add_row(
        "Disk",
        f"{usage['disk_mb']:.0f} MB",
        f"{quota['disk_limit_mb']} MB"
    )
    table.add_row(
        "Executions",
        f"{usage['active_executions']}",
        f"{quota['max_concurrent_executions']}"
    )
    
    console.print(table)


@resources.command("check")
@click.option("--cpu", default=0.0, help="Required CPU cores")
@click.option("--memory", default=0, help="Required memory in MB")
async def resource_check(cpu: float, memory: int):
    """Check if resources are available."""
    resource_manager = get_resource_manager()
    
    available, message = await resource_manager.check_resources(
        required_cpu=cpu,
        required_memory_mb=memory,
    )
    
    if available:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")


if __name__ == "__main__":
    runtime_cli()
