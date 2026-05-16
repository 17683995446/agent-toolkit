"""CLI commands for Tool Orchestrator."""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from agent_toolkit.orchestrator.orchestration_models import ToolChain, ExecutionMode
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
from agent_toolkit.orchestrator.task_scheduler import Scheduler, ScheduleType
from agent_toolkit.shared.structured_logging import setup_logging, get_logger

console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def orchestrator_cli(debug: bool):
    """Tool Orchestrator CLI."""
    setup_logging(level="DEBUG" if debug else "INFO")


@orchestrator_cli.group("chain")
def chain():
    """Tool chain management."""
    pass


@chain.command("create")
@click.option("--name", required=True, help="Chain name")
@click.option("--description", help="Chain description")
@click.option("--mode", type=click.Choice(["sequential", "parallel", "dag"]), default="sequential")
def chain_create(name: str, description: Optional[str], mode: str):
    """Create a new tool chain."""
    console.print(f"[cyan]Creating tool chain:[/cyan] {name}")
    console.print(f"Execution mode: {mode}")
    if description:
        console.print(f"Description: {description}")


@chain.command("list")
def chain_list():
    """List all tool chains."""
    table = Table(title="Tool Chains")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Mode", style="yellow")
    table.add_column("Status", style="magenta")
    
    table.add_row("chain-1", "Search Process Chain", "sequential", "active")
    table.add_row("chain-2", "Data Pipeline", "parallel", "draft")
    
    console.print(table)


@chain.command("info")
@click.argument("chain_id")
def chain_info(chain_id: str):
    """Get tool chain details."""
    console.print(f"[cyan]Chain ID:[/cyan] {chain_id}")


@chain.command("execute")
@click.argument("chain_id")
@click.option("--input", "-i", help="Input JSON file")
def chain_execute(chain_id: str, input: Optional[str]):
    """Execute a tool chain."""
    console.print(f"[cyan]Executing chain:[/cyan] {chain_id}")
    if input:
        console.print(f"Input file: {input}")


@orchestrator_cli.group("schedule")
def schedule():
    """Schedule management."""
    pass


@schedule.command("list")
def schedule_list():
    """List all schedules."""
    table = Table(title="Schedules")
    table.add_column("ID", style="cyan")
    table.add_column("Chain", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="magenta")
    
    table.add_row("sched-1", "chain-1", "interval", "active")
    
    console.print(table)


@schedule.command("create")
@click.argument("chain_id")
@click.option("--type", type=click.Choice(["immediate", "delayed", "interval", "cron"]), default="immediate")
def schedule_create(chain_id: str, type: str):
    """Create a new schedule."""
    console.print(f"[cyan]Creating schedule for chain:[/cyan] {chain_id}")
    console.print(f"Schedule type: {type}")


@schedule.command("delete")
@click.argument("schedule_id")
def schedule_delete(schedule_id: str):
    """Delete a schedule."""
    console.print(f"[red]Deleting schedule:[/red] {schedule_id}")


@orchestrator_cli.command("status")
def status():
    """Show orchestrator status."""
    console.print("[cyan]Orchestrator Status:[/cyan]")
    console.print("Status: [green]running[/green]")
    console.print("Active executions: 0")
    console.print("Queued: 0")


if __name__ == "__main__":
    orchestrator_cli()
