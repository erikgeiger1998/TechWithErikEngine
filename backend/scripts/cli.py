#!/usr/bin/env python3

import typer
import asyncio
from app.connectors.apple_newsroom import AppleNewsroomConnector
from app.services.signal_bus import SignalBus
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Tech With Erik - Editorial Intelligence OS CLI")
console = Console()

@app.command("friction")
def friction():
    """
    Displays the Top Human Problems Today based on current ingestion data.
    """
    console.print(Panel("[bold cyan]TOP HUMAN PROBLEMS TODAY[/bold cyan]", expand=False))
    
    # In a full implementation, this will query the PostgreSQL 'problems' and 'opportunities' tables.
    # For MVP v1 CLI verification, we demonstrate the requested UX layout.
    
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold white", width=20)
    table.add_column("Value", style="yellow")
    
    console.print("\n[bold white]1. PHONE_OVERHEATING[/bold white]")
    table.add_row("Demand:", "[green]↑ 240%[/green]")
    table.add_row("Evidence:", "Google Trends, Reddit, Weather API")
    table.add_row("Visual Proof:", "[green]YES[/green]")
    table.add_row("ROI:", "[bold cyan]9.6[/bold cyan]")
    table.add_row("Recommendation:", "[bold green]FILM TODAY[/bold green]")
    console.print(table)
    
    console.print("\n[dim]--------------------------------[/dim]\n")
    
    table2 = Table(show_header=False, box=None)
    table2.add_column("Key", style="bold white", width=20)
    table2.add_column("Value", style="yellow")
    
    console.print("[bold white]2. QR_PHISHING[/bold white]")
    table2.add_row("Demand:", "[green]↑ 110%[/green]")
    table2.add_row("Evidence:", "DNSC Alert")
    table2.add_row("Visual Proof:", "[green]YES[/green]")
    table2.add_row("ROI:", "[bold cyan]8.9[/bold cyan]")
    table2.add_row("Recommendation:", "[bold yellow]WATCH[/bold yellow]")
    console.print(table2)

@app.command()
def fetch(source: str):
    """
    Fetch data from connectors.
    """

    if source == "apple":
        signal_bus = SignalBus()
        connector = AppleNewsroomConnector(signal_bus)

        print("Fetching Apple Newsroom...")

        result = asyncio.run(connector.fetch())

        print(result)

    else:
        print(f"Unknown connector: {source}")

@app.command("morning")
def morning():
    """
    Generates the Daily Editorial Brief.
    """
    console.print("[bold magenta]Fetching today's intelligence...[/bold magenta]")
    friction()

if __name__ == "__main__":
    app()
