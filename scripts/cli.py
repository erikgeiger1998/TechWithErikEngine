#!/usr/bin/env python3

import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from app.database.connection import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.services.editorial import EditorialEngine

app = typer.Typer(help="Tech With Erik - Editorial Intelligence OS CLI")
console = Console()

def run_async(coro):
    return asyncio.run(coro)

@app.command("fetch")
def fetch(source: str):
    """
    Fetch data from connectors. source can be 'apple', 'apple_support', 'dnsc', 'autocomplete', 'trends', or 'all'.
    """
    async def _fetch():
        async with AsyncSessionLocal() as db:
            service = IngestionService(db)
            await service.fetch(source)
            
    run_async(_fetch())
    console.print(f"[bold green]Successfully ran ingestion for {source}[/bold green]")

@app.command("health")
def health():
    """
    Show health status of all connectors.
    """
    async def _health():
        async with AsyncSessionLocal() as db:
            service = IngestionService(db)
            table = Table(title="Connector Health Status")
            table.add_column("Connector", style="cyan", no_wrap=True)
            table.add_column("Status", style="magenta")
            table.add_column("Latency (ms)", justify="right", style="green")
            table.add_column("Errors", justify="right", style="red")

            for name, connector in service.connectors.items():
                health_data = await connector.health()
                status = health_data.get("status", "Unknown")
                latency = str(round(health_data.get("latency_ms", 0), 2))
                errors = str(health_data.get("errors", 0))
                
                if status == "Healthy":
                    status_col = f"[green]{status}[/green]"
                else:
                    status_col = f"[red]{status}[/red]"
                    
                table.add_row(name, status_col, latency, errors)
                
            console.print(table)
            
    run_async(_health())

@app.command("morning")
def morning():
    """
    Generates the Daily Editorial Brief using real database data.
    """
    async def _morning():
        console.print("[bold magenta]Fetching today's intelligence...[/bold magenta]\n")
        
        async with AsyncSessionLocal() as db:
            engine = EditorialEngine(db)
            recommendations = await engine.generate_morning_recommendations()
            
            if not recommendations:
                console.print("[yellow]No problems found in the database to recommend.[/yellow]")
                return

            console.print(Panel("[bold cyan]EDITORIAL RECOMMENDATIONS TODAY[/bold cyan]", expand=False))
            
            for idx, rec in enumerate(recommendations, 1):
                table = Table(show_header=False, box=None)
                table.add_column("Key", style="bold white", width=20)
                table.add_column("Value", style="yellow")
                
                table.add_row("Topic:", rec.topic)
                
                decision_color = "green" if rec.film_decision else "red"
                decision_str = "YES" if rec.film_decision else "NO"
                table.add_row("Film:", f"[{decision_color}]{decision_str}[/{decision_color}]")
                
                table.add_row("Confidence:", f"{rec.confidence_percentage:.1f}%")
                table.add_row("Trust Score:", str(rec.trust_score))
                table.add_row("Reasoning:", rec.reasoning)
                
                console.print(f"[bold white]{idx}. {rec.topic.upper()}[/bold white]")
                console.print(table)
                console.print("\n[dim]--------------------------------[/dim]\n")
                
    run_async(_morning())

@app.command("explain")
def explain(topic: str):
    console.print(f"Explaining topic: {topic} (Not fully implemented yet)")

@app.command("problems")
def problems():
    console.print("Listing problems... (Not fully implemented yet)")

@app.command("recommendations")
def recommendations():
    console.print("Listing past recommendations... (Not fully implemented yet)")

@app.command("sources")
def sources():
    console.print("Listing sources... (Not fully implemented yet)")

if __name__ == "__main__":
    app()
