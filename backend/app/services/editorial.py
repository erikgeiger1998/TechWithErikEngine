import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.problem import Problem
from app.models.signal import Signal
from app.models.recommendation import Recommendation, HumanDecision
from app.models.opportunity import Opportunity

logger = logging.getLogger(__name__)

class EditorialEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_evidence_decay(self, signal: Signal) -> float:
        """
        Decay the value of older signals.
        If a signal is older than 7 days, its weight decays exponentially.
        """
        if not signal.created_at:
            return 1.0
            
        now = datetime.now(timezone.utc)
        created_utc = signal.created_at
        if created_utc.tzinfo is None:
            created_utc = created_utc.replace(tzinfo=timezone.utc)
            
        age_days = (now - created_utc).days
        
        # Simple decay: full weight for 7 days, then halve every 7 days.
        if age_days <= 7:
            return 1.0
        return 0.5 ** ((age_days - 7) / 7.0)

    async def calculate_roi(self, problem: Problem) -> tuple[float, float]:
        """
        Calculates ROI deterministically:
        ROI = Impact * Trust * Demand * Production Ease
        """
        # fixed heuristics per problem for MVP (in real app, this would be on Problem model)
        # Impact: 1-10 scale
        # Production Ease: 1-10 scale
        
        impact = problem.severity if problem.severity else 5.0
        production_ease = problem.production_ease if problem.production_ease else 7.0
        seasonality = problem.seasonality_multiplier if problem.seasonality_multiplier else 1.0
        
        demand_score = 0.0
        trust_score = 0.0
        
        total_signals = 0
        total_trust = 0.0
        
        for signal in problem.signals:
            decay = self.calculate_evidence_decay(signal)
            
            # Demand calculation
            if signal.category == "Demand" or signal.category == "Friction":
                demand_score += signal.importance * decay
            
            # Trust calculation (Official sources)
            if signal.reliability > 0:
                total_trust += signal.reliability * decay
                total_signals += 1
                
        # Average trust or fallback to 1.0 if no trust signals
        trust = (total_trust / total_signals) if total_signals > 0 else 1.0
        
        # Normalize demand to a 1-10 multiplier (assuming max demand score ~1000)
        demand_multiplier = min(demand_score / 100.0, 10.0)
        if demand_multiplier < 1.0:
            demand_multiplier = 1.0
            
        # Normalize trust to 1-10 multiplier
        trust_multiplier = trust / 10.0
        
        # Apply seasonality modifier
        roi = impact * trust_multiplier * demand_multiplier * production_ease * seasonality
        return round(roi, 2), round(trust, 2)

    async def generate_morning_recommendations(self):
        """
        Scans all Problems, calculates ROI, and creates historical Recommendation snapshots.
        """
        stmt = select(Problem).options(selectinload(Problem.signals), selectinload(Problem.opportunity))
        result = await self.db.execute(stmt)
        problems = result.scalars().all()
        
        recommendations = []
        
        for problem in problems:
            roi, trust = await self.calculate_roi(problem)
            
            # Ensure Opportunity exists
            opp = problem.opportunity
            if not opp:
                opp = Opportunity(
                    problem_id=problem.id,
                    why=f"Automatically generated based on high signal velocity for {problem.name}."
                )
                self.db.add(opp)
                await self.db.commit()
                await self.db.refresh(opp)
            
            # Create a recommendation snapshot
            confidence = min(roi / 10.0, 100.0) # Dummy scaling for MVP
            
            trust_risk = "LOW" if trust >= 7.5 else "HIGH" if trust < 4.0 else "MEDIUM"
            
            rec = Recommendation(
                opportunity_id=opp.id,
                film_decision=roi > 500, # arbitrary threshold
                topic=opp.title,
                confidence_percentage=confidence,
                trust_score=trust,
                reasoning=f"ROI is {roi}, calculated deterministically.",
                erik_decision=HumanDecision.PENDING
            )
            
            self.db.add(rec)
            recommendations.append(rec)
            
        await self.db.commit()
        return recommendations
