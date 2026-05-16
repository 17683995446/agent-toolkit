"""CLI commands for Tool Registry."""

import asyncio
import json
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent_toolkit.shared.application_settings import get_settings
from agent_toolkit.shared.database_connection import get_db_session_context, init_db
from agent_toolkit.shared.structured_logging import setup_logging, get_logger
from agent_toolkit.registry.registry_service import (
    ToolService, ToolVersionService, ToolCategoryService, RegistryStatsService
)
from agent_toolkit.registry.registry_schemas import (
    ToolCreate, ToolUpdate, ToolVersionCreate, ToolCategoryCreate, ToolCategoryUpdate
)

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--config", type=click.Path(exists=True), help="Config file path")
def registry_cli(debug: bool, config: Optional[str]):
    """Agent Toolkit Registry CLI."""
    setup_logging(level="DEBUG" if debug else "INFO")


@registry_cli.command()
async def init():
    """Initialize the database."""
    console.print("[cyan]Initializing database...[/cyan]")
    try:
        await init_db()
        console.print("[green]✓ Database initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize database: {e}[/red]")
        raise click.Abort()


@registry_cli.group()
def tools():
    """Manage tools."""
    pass


@tools.command("list")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--status", help="Filter by status")
@click.option("--category", type=int, help="Filter by category ID")
@click.option("--search", help="Search query")
async def list_tools(page: int, page_size: int, status: Optional[str], category: Optional[int], search: Optional[str]):
    """List all tools."""
    async with get_db_session_context() as session:
        service = ToolService(session)
        tools_list, total = await service.list_tools(
            page=page,
            page_size=page_size,
            status=status,
            category_id=category,
            search=search
        )

    table = Table(title=f"Tools (Total: {total})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Author", style="blue")

    for tool in tools_list:
        table.add_row(
            str(tool.id),
            tool.name,
            tool.version,
            tool.status,
            tool.author
        )

    console.print(table)
    console.print(f"\nPage {page}/{max(1, (total + page_size - 1) // page_size)}")


@tools.command("create")
@click.option("--name", required=True, help="Tool name")
@click.option("--description", required=True, help="Tool description")
@click.option("--version", default="1.0.0", help="Tool version")
@click.option("--author", required=True, help="Tool author")
@click.option("--adapter-type", required=True, type=click.Choice(["http", "cli", "sdk", "function"]), help="Adapter type")
@click.option("--input-schema", type=str, help="Input schema JSON file")
async def create_tool(name: str, description: str, version: str, author: str, adapter_type: str, input_schema: Optional[str]):
    """Create a new tool."""
    input_schema_dict = {}
    if input_schema:
        with open(input_schema) as f:
            input_schema_dict = json.load(f)

    tool_data = ToolCreate(
        name=name,
        description=description,
        version=version,
        author=author,
        adapter_type=adapter_type,
        adapter_config={},
        input_schema=input_schema_dict
    )

    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            tool = await service.create_tool(tool_data)
            console.print(f"[green]✓ Tool '{tool.name}' created successfully (ID: {tool.id})[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to create tool: {e}[/red]")
            raise click.Abort()


@tools.command("info")
@click.argument("tool_id", type=int)
async def tool_info(tool_id: int):
    """Get tool information."""
    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            tool = await service.get_tool(tool_id)
            console.print(f"\n[cyan]Tool: {tool.name}[/cyan]")
            console.print(f"ID: {tool.id}")
            console.print(f"Version: {tool.version}")
            console.print(f"Status: {tool.status}")
            console.print(f"Author: {tool.author}")
            console.print(f"Description: {tool.description}")
            console.print(f"Usage Count: {tool.usage_count}")
            if tool.rating:
                console.print(f"Rating: {tool.rating:.1f}/5")
        except Exception as e:
            console.print(f"[red]✗ Tool not found: {e}[/red]")
            raise click.Abort()


@tools.command("update")
@click.argument("tool_id", type=int)
@click.option("--description", help="New description")
@click.option("--version", help="New version")
async def update_tool(tool_id: int, description: Optional[str], version: Optional[str]):
    """Update a tool."""
    update_data = ToolUpdate()
    if description:
        update_data.description = description
    if version:
        update_data.version = version

    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            tool = await service.update_tool(tool_id, update_data)
            console.print(f"[green]✓ Tool '{tool.name}' updated successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to update tool: {e}[/red]")
            raise click.Abort()


@tools.command("delete")
@click.argument("tool_id", type=int)
@click.option("--force", is_flag=True, help="Force delete without confirmation")
async def delete_tool(tool_id: int, force: bool):
    """Delete a tool."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete tool {tool_id}?"):
            return

    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            await service.delete_tool(tool_id)
            console.print(f"[green]✓ Tool {tool_id} deleted successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to delete tool: {e}[/red]")
            raise click.Abort()


@tools.command("activate")
@click.argument("tool_id", type=int)
async def activate_tool(tool_id: int):
    """Activate a tool."""
    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            tool = await service.activate_tool(tool_id)
            console.print(f"[green]✓ Tool '{tool.name}' activated[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to activate tool: {e}[/red]")
            raise click.Abort()


@tools.command("deprecate")
@click.argument("tool_id", type=int)
async def deprecate_tool(tool_id: int):
    """Deprecate a tool."""
    async with get_db_session_context() as session:
        service = ToolService(session)
        try:
            tool = await service.deprecate_tool(tool_id)
            console.print(f"[green]✓ Tool '{tool.name}' deprecated[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to deprecate tool: {e}[/red]")
            raise click.Abort()


@registry_cli.group()
def categories():
    """Manage categories."""
    pass


@categories.command("list")
async def list_categories():
    """List all categories."""
    async with get_db_session_context() as session:
        service = ToolCategoryService(session)
        categories_list = await service.list_categories()

    table = Table(title="Categories")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="yellow")

    for cat in categories_list:
        table.add_row(str(cat.id), cat.name, cat.description or "")

    console.print(table)


@categories.command("create")
@click.option("--name", required=True, help="Category name")
@click.option("--description", help="Category description")
async def create_category(name: str, description: Optional[str]):
    """Create a new category."""
    category_data = ToolCategoryCreate(name=name, description=description)

    async with get_db_session_context() as session:
        service = ToolCategoryService(session)
        try:
            category = await service.create_category(category_data)
            console.print(f"[green]✓ Category '{category.name}' created (ID: {category.id})[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to create category: {e}[/red]")
            raise click.Abort()


@registry_cli.command("stats")
async def stats():
    """Show registry statistics."""
    async with get_db_session_context() as session:
        service = RegistryStatsService(session)
        stats_data = await service.get_stats()

    console.print("\n[cyan]Registry Statistics[/cyan]")
    console.print(f"Total Tools: {stats_data['total_tools']}")
    console.print(f"Active Tools: {stats_data['active_tools']}")
    console.print(f"Deprecated Tools: {stats_data['deprecated_tools']}")
    console.print(f"Total Downloads: {stats_data['total_downloads']}")
    if stats_data['average_rating']:
        console.print(f"Average Rating: {stats_data['average_rating']:.2f}/5")


if __name__ == "__main__":
    registry_cli()
