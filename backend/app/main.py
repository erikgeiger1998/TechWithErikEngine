from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime

from app.core.config import settings
from app.database.connection import AsyncSessionLocal
from app.models.signal import Signal
from app.models.problem import Problem
from app.models.recommendation import Recommendation
from app.models.connector_health import ConnectorHealth
from app.services.scheduler import SchedulerService
from contextlib import asynccontextmanager

scheduler_service = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler_service.start()
    yield
    # Shutdown
    scheduler_service.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    signals_count = (await db.execute(select(func.count(Signal.id)))).scalar() or 0
    problems_count = (await db.execute(select(func.count(Problem.id)))).scalar() or 0
    rec_count = (await db.execute(select(func.count(Recommendation.id)))).scalar() or 0
    
    health_records = (await db.execute(select(ConnectorHealth))).scalars().all()
    healthy_count = sum(1 for r in health_records if r.status and r.status.value == "HEALTHY")
    warning_count = sum(1 for r in health_records if r.status and r.status.value == "WARNING")
    
    last_fetch = max((r.last_run for r in health_records if r.last_run), default=None)
    last_fetch_str = last_fetch.strftime("%Y-%m-%d %H:%M:%S") if last_fetch else "Never"
    
    connectors = []
    for r in health_records:
        connectors.append({
            "name": r.connector_name,
            "status": r.status.value if r.status else "UNKNOWN",
            "last_success": r.last_success.strftime("%H:%M") if r.last_success else "-",
            "last_failure": r.last_failure.strftime("%H:%M") if r.last_failure else "-",
            "latency_ms": r.latency_ms,
            "items_processed": r.items_processed
        })
    
    return {
        "database": {
            "signals": signals_count,
            "problems": problems_count,
            "recommendations": rec_count
        },
        "connectors_summary": {
            "healthy": healthy_count,
            "warnings": warning_count,
            "last_fetch": last_fetch_str
        },
        "connectors": connectors
    }

@app.get("/api/recommendations/today")
async def get_todays_recommendation(db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    from app.models.opportunity import Opportunity
    
    stmt = (
        select(Recommendation)
        .options(
            selectinload(Recommendation.opportunity)
            .selectinload(Opportunity.problem)
            .selectinload(Problem.signals)
        )
        .order_by(Recommendation.confidence_percentage.desc())
        .limit(1)
    )
    top_rec = (await db.execute(stmt)).scalars().first()
    
    if not top_rec:
        return {"topic": "No recommendations yet", "roi": 0.0, "film_decision": False, "trust_risk": "UNKNOWN", "evidence": []}
        
    roi = round(top_rec.confidence_percentage / 10.0, 1)
    trust_risk = "LOW" if top_rec.trust_score >= 7.5 else "HIGH" if top_rec.trust_score < 4.0 else "MEDIUM"
    
    evidence_list = []
    if top_rec.opportunity and top_rec.opportunity.problem:
        # Take the top 3 signals as evidence
        for sig in top_rec.opportunity.problem.signals[:3]:
            evidence_list.append({
                "source": sig.source_name,
                "type": sig.category or "Evidence"
            })
            
    if not evidence_list:
        evidence_list = [{"source": "Historical", "type": "Generated Opportunity"}]
    
    return {
        "topic": top_rec.topic,
        "roi": roi,
        "film_decision": top_rec.film_decision,
        "confidence": top_rec.confidence_percentage,
        "trust_risk": trust_risk,
        "evidence": evidence_list
    }

@app.get("/api/intelligence/problems")
async def get_problems(db: AsyncSession = Depends(get_db)):
    stmt = select(Problem).order_by(Problem.evergreen_score.desc())
    result = await db.execute(stmt)
    problems = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "aliases": p.aliases,
            "evergreen_score": p.evergreen_score,
            "seasonality_multiplier": p.seasonality_multiplier,
            "production_ease": p.production_ease,
            "base_audience_size": p.base_audience_size
        } for p in problems
    ]
