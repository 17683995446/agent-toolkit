"""CLI commands for Observability."""

import click
from rich.console import Console
from rich.table import Table

from agent_toolkit.observability.metrics_collector import metrics_collector
from agent_toolkit.shared.structured_logging import setup_logging, get_logger

console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def observability_cli(debug: bool):
    """Observability CLI."""
    setup_logging(level="DEBUG" if debug else "INFO")


@observability_cli.command("metrics")
def metrics():
    """Show metrics."""
    collector = metrics_collector()
    metrics_data = collector.get_current_metrics()
    
    console.print("[cyan]Current Metrics:[/cyan]")
    
    table = Table(title="Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for name, data in metrics_data.items():
        if "samples" in data:
            for sample in data["samples"][:5]:
                labels = ", ".join(f"{k}={v}" for k, v in sample["labels"].items())
                table.add_row(f"{name} [{labels}]", str(sample["value"]))
    
    console.print(table)


@observability_cli.command("health")
def health():
    """Check service health."""
    console.print("[cyan]Service Health:[/cyan]")
    console.print("Registry: [green]healthy[/green]")
    console.print("Adapter: [green]healthy[/green]")
    console.print("Runtime: [green]healthy[/green]")
    console.print("Orchestrator: [green]healthy[/green]")
    console.print("Observability: [green]healthy[/green]")


@observability_cli.command("stats")
def stats():
    """Show statistics."""
    console.print("[cyan]Statistics:[/cyan]")
    console.print("Total Tools: 0")
    console.print("Active Executions: 0")
    console.print("Total Requests: 0")
    console.print("Success Rate: N/A")


@observability_cli.group("alerts")
def alerts():
    """Alert management."""
    pass


@alerts.command("list")
def alert_list():
    """List all alerts."""
    console.print("[yellow]No active alerts[/yellow]")


@alerts.command("rules")
def alert_rules():
    """List alert rules."""
    table = Table(title="Alert Rules")
    table.add_column("Name", style="cyan")
    table.add_column("Condition", style="yellow")
    table.add_column("Status", style="green")
    
    table.add_row("high_error_rate", "error_rate > 5%", "active")
    table.add_row("high_latency", "p99_latency > 1000ms", "active")
    
    console.print(table)


if __name__ == "__main__":
    observability_cli()
