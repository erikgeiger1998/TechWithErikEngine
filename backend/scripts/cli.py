#!/usr/bin/env python3

import typer
import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sqlalchemy.future import select

from app.database.connection import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.services.editorial import EditorialEngine
from app.models.connector_health import ConnectorHealth

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
            summary = await service.fetch(source)
            
            console.print("\n[bold cyan]──────── Ingestion Summary ────────[/bold cyan]")
            
            for name, details in summary["details"].items():
                status = details["status"]
                items = details["items"]
                error = details["error"]
                
                if status == "HEALTHY":
                    console.print(f"[green]✓ {name.ljust(20)} {items} items[/green]")
                elif status == "WARNING":
                    msg = error if error else "Warning"
                    # Only show up to ~20 chars of error
                    console.print(f"[yellow]⚠ {name.ljust(20)} {msg[:30]}[/yellow]")
                elif status == "DISABLED":
                    console.print(f"[yellow]⚠ {name.ljust(20)} Disabled[/yellow]")
                else:
                    msg = error if error else "Failed"
                    console.print(f"[red]✗ {name.ljust(20)} {msg[:30]}[/red]")
            
            console.print("[bold cyan]──────────────────────────────────[/bold cyan]")
            console.print(f"Processed: {summary['processed']}")
            console.print(f"Healthy:   {summary['healthy']}")
            console.print(f"Warnings:  {summary['warnings']}")
            console.print(f"Failures:  {summary['failures']}")
            console.print(f"Duration:  {summary['duration_s']:.2f} s\n")

    run_async(_fetch())

def _format_time(dt: datetime) -> str:
    if not dt:
        return "-"
    return dt.strftime("%H:%M")

@app.command("health")
def health():
    """
    Show health status of all connectors from the database history.
    """
    async def _health():
        async with AsyncSessionLocal() as db:
            stmt = select(ConnectorHealth).order_by(ConnectorHealth.connector_name)
            result = await db.execute(stmt)
            records = result.scalars().all()
            
            table = Table(title="Connector Health Status")
            table.add_column("Connector", style="cyan", no_wrap=True)
            table.add_column("Status", style="bold")
            table.add_column("Last Success", justify="center")
            table.add_column("Last Failure", justify="center")
            table.add_column("HTTP", justify="center")
            table.add_column("Latency", justify="right")
            table.add_column("Items", justify="right")
            table.add_column("Duplicates", justify="right")

            if not records:
                console.print("[yellow]No connector health data found. Run an ingestion first.[/yellow]")
                return

            for rec in records:
                status_val = rec.status.value if rec.status else "UNKNOWN"
                if status_val == "HEALTHY":
                    status_col = f"[green]HEALTHY[/green]"
                elif status_val == "WARNING":
                    status_col = f"[yellow]WARNING[/yellow]"
                elif status_val == "FAILED":
                    status_col = f"[red]FAILED[/red]"
                else:
                    status_col = f"[dim]{status_val}[/dim]"
                
                latency_str = f"{rec.latency_ms:.0f} ms" if rec.latency_ms is not None else "-"
                
                table.add_row(
                    rec.connector_name,
                    status_col,
                    _format_time(rec.last_success),
                    _format_time(rec.last_failure),
                    rec.http_status or "-",
                    latency_str,
                    str(rec.items_processed),
                    str(rec.duplicates)
                )
                
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
