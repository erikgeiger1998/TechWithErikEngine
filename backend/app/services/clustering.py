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
    async def determine_problem(cls, db_session: AsyncSession, text: str) -> Optional[str]:
        """
        Attempts to map text to a canonical Problem node using DB aliases.
        """
        text_lower = text.lower()
        mapping = await cls.get_problems_map(db_session)
        
        for canonical_name, aliases in mapping.items():
            for alias in aliases:
                if alias in text_lower:
                    return canonical_name
                    
        return None

    @classmethod
    async def attach_signal(cls, db_session: AsyncSession, signal: dict) -> None:
        """
        Looks up or creates a Problem and associates the Signal.
        """
        # (Mock implementation for now, should accept the actual Signal ORM object)
        text_to_analyze = signal.get("title", "") + " " + signal.get("summary", "")
        problem_name = await cls.determine_problem(db_session, text_to_analyze)
        
        if problem_name:
            logger.info(f"[CLUSTERING] Mapped signal to {problem_name}")
        else:
            logger.debug(f"[CLUSTERING] Unmapped signal: {text_to_analyze[:30]}...")

