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
from app.models.signal import Signal
from app.models.problem import Problem
from app.models.recommendation import Recommendation
from sqlalchemy import func

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

@app.command("dashboard")
def dashboard():
    """
    Shows a Bloomberg-terminal style dashboard for the Editorial OS.
    """
    async def _dashboard():
        async with AsyncSessionLocal() as db:
            # Counts
            signals_count = (await db.execute(select(func.count(Signal.id)))).scalar() or 0
            problems_count = (await db.execute(select(func.count(Problem.id)))).scalar() or 0
            rec_count = (await db.execute(select(func.count(Recommendation.id)))).scalar() or 0
            
            # Connector Health
            health_records = (await db.execute(select(ConnectorHealth))).scalars().all()
            healthy_count = sum(1 for r in health_records if r.status and r.status.value == "HEALTHY")
            warning_count = sum(1 for r in health_records if r.status and r.status.value == "WARNING")
            
            last_fetch = max((r.last_run for r in health_records if r.last_run), default=None)
            last_fetch_str = _format_time(last_fetch) if last_fetch else "Never"
            
            # Top Problem & ROI (based on Recommendations)
            stmt = select(Recommendation).order_by(Recommendation.confidence_percentage.desc()).limit(1)
            top_rec = (await db.execute(stmt)).scalars().first()
            
            top_problem_str = top_rec.topic if top_rec else "None"
            top_roi_str = str(round(top_rec.confidence_percentage / 10.0, 1)) if top_rec else "0.0"
            
            panel_content = f"""[bold cyan]Database[/bold cyan]
Signals:          {signals_count:,}
Problems:         {problems_count:,}
Recommendations:  {rec_count:,}

[bold cyan]Connectors[/bold cyan]
Healthy:          {healthy_count}
Warnings:         {warning_count}
Last Fetch:       {last_fetch_str}

[bold cyan]Intelligence[/bold cyan]
Top Problem:      {top_problem_str}
Top ROI:          {top_roi_str}"""

            console.print(Panel(panel_content, title="[bold white]Editorial OS Dashboard[/bold white]", expand=False))
            
    run_async(_dashboard())

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

@app.command()
def seed():
    """
    Seeds the database with canonical Tech problems for Romania.
    """
    async def _seed():
        async with AsyncSessionLocal() as db:
            problems_to_seed = [
                {"name": "iPhone Battery Drain", "aliases": ["iphone battery", "battery life", "drain", "ios 18 battery"]},
                {"name": "iPhone Overheating", "aliases": ["iphone 15 pro hot", "overheating", "temperature", "supraincalzire"]},
                {"name": "Samsung Screen Issues", "aliases": ["samsung screen", "green line", "oled burn", "ecran verde"]},
                {"name": "Android OneUI Stutter", "aliases": ["oneui lag", "stutter", "samsung lag", "incet"]},
                {"name": "iOS Update Bugs", "aliases": ["ios bug", "update problem", "wifi drop", "bluetooth disconnect"]},
                {"name": "Hidden iOS Tricks", "aliases": ["ios trick", "iphone hidden", "secret feature", "tips"]},
                {"name": "Hidden Samsung Tricks", "aliases": ["samsung trick", "galaxy hidden", "good lock", "tips"]},
                {"name": "Cybersecurity Scams (DNSC)", "aliases": ["dnsc", "phishing", "scam", "frauda", "smishing"]},
                {"name": "Tech Deals & Advice", "aliases": ["emag deal", "altex reduceri", "best phone", "ce telefon sa cumpar"]}
            ]
            
            for p_data in problems_to_seed:
                # Check if exists
                result = await db.execute(select(Problem).where(Problem.name == p_data["name"]))
                existing = result.scalars().first()
                if not existing:
                    new_prob = Problem(name=p_data["name"], aliases=p_data["aliases"])
                    db.add(new_prob)
                    
            await db.commit()
            
    asyncio.run(_seed())
    print("[+] Database successfully seeded with canonical problems!")

if __name__ == "__main__":
    app()
