import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.published_video import PublishedVideo
from app.models.problem import Problem
from app.services.clustering import ProblemClusteringEngine

logger = logging.getLogger(__name__)

class HistoricalLearningEngine:
    """
    Automated feedback loop. Analyzes the newly fetched PublishedVideos,
    maps them to canonical Problems, and adjusts the evergreen_score.
    """
    
    @classmethod
    async def process_fetched_videos(cls, db: AsyncSession, raw_videos: list[dict]):
        """
        Inserts new videos and updates existing ones with latest views.
        Then runs the learning loop to adjust Problem ROI modifiers.
        """
        if not raw_videos:
            return
            
        for v_data in raw_videos:
            # 1. Map video to a Problem using Clustering Engine
            text_to_analyze = f"{v_data['title']}"
            problem_id = await ProblemClusteringEngine.determine_problem(db, text_to_analyze)
            
            # 2. Upsert PublishedVideo
            stmt = select(PublishedVideo).where(PublishedVideo.video_url == v_data['url'])
            existing = (await db.execute(stmt)).scalars().first()
            
            if existing:
                # Update views if they increased
                if v_data['views'] > existing.views:
                    existing.views = v_data['views']
            else:
                new_video = PublishedVideo(
                    problem_id=problem_id,
                    video_url=v_data['url'],
                    title=v_data['title'],
                    views=v_data['views'],
                    likes=v_data['likes'],
                    published_at=v_data['published_at']
                )
                db.add(new_video)
                
        await db.commit()
        
        # 3. Run Learning Adjustments
        await cls.run_learning_loop(db)

    @classmethod
    async def run_learning_loop(cls, db: AsyncSession):
        """
        Analyzes all problems. If a problem has published videos,
        it evaluates their performance and adjusts the evergreen_score deterministically.
        """
        stmt = select(Problem).options(selectinload(Problem.videos))
        problems = (await db.execute(stmt)).scalars().all()
        
        for problem in problems:
            if not problem.videos:
                continue
                
            total_views = sum(v.views for v in problem.videos)
            avg_views = total_views / len(problem.videos)
            
            # Deterministic Learning Rule:
            # If average views on this topic exceed a threshold (e.g., 100k), 
            # permanently boost its evergreen score so it gets recommended more.
            # (Threshold is low for MVP testing)
            if avg_views > 1000:
                new_score = min(10.0, problem.evergreen_score + 1.5)
                if problem.evergreen_score != new_score:
                    logger.info(f"[LEARNING] Boosting {problem.name} evergreen_score to {new_score} due to high historical views ({avg_views}).")
                    problem.evergreen_score = new_score
            
        await db.commit()
