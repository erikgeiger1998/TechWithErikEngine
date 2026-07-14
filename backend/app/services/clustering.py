import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ProblemClusteringEngine:
    """
    Deterministic Problem Clustering Engine (MVP v1).
    Maps unstructured human friction (queries, titles) to canonical Problem nodes.
    Uses strict keyword mapping and aliases rather than AI embeddings.
    """
    
    @classmethod
    async def get_problems_map(cls, db_session: AsyncSession) -> Dict[str, List[str]]:
        """
        Loads all Problem names and aliases from the DB into a mapping.
        """
        from app.models.problem import Problem
        from sqlalchemy.future import select
        
        stmt = select(Problem)
        result = await db_session.execute(stmt)
        problems = result.scalars().all()
        
        mapping = {}
        for p in problems:
            # combine name with explicit aliases
            aliases = [p.name.lower()]
            if p.aliases:
                aliases.extend([a.lower() for a in p.aliases])
            mapping[p.name] = aliases
            
        return mapping

    @classmethod
    async def determine_problem(cls, db_session: AsyncSession, text: str) -> Optional[int]:
        """
        Attempts to map text to a canonical Problem node using DB aliases.
        Returns the Problem ID if a match is found.
        """
        text_lower = text.lower()
        
        from app.models.problem import Problem
        from sqlalchemy.future import select
        
        stmt = select(Problem)
        result = await db_session.execute(stmt)
        problems = result.scalars().all()
        
        for p in problems:
            aliases = [p.name.lower()]
            if p.aliases:
                aliases.extend([a.lower() for a in p.aliases])
                
            for alias in aliases:
                # Basic token matching could be improved with regex/NLP later
                if alias in text_lower:
                    return p.id
                    
        return None

    @classmethod
    async def attach_signal(cls, db_session: AsyncSession, signal) -> None:
        """
        Associates the Signal ORM object with a canonical Problem.
        """
        from app.models.signal import Signal
        if not isinstance(signal, Signal):
            return
            
        text_to_analyze = f"{signal.title} {signal.summary or ''} {signal.url}"
        problem_id = await cls.determine_problem(db_session, text_to_analyze)
        
        if problem_id:
            signal.problem_id = problem_id
            db_session.add(signal)
            await db_session.commit()
            logger.info(f"[CLUSTERING] Mapped signal '{signal.title[:20]}...' to Problem {problem_id}")
        else:
            logger.debug(f"[CLUSTERING] Unmapped signal: {signal.title[:30]}...")

