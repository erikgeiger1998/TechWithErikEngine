import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.future import select

from app.database.connection import AsyncSessionLocal
from app.models.recommendation import Recommendation
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)

async def run_morning_brief_job():
    """
    Job that fires at 7:00 AM. 
    It queries the latest top recommendations from the database and emails them.
    """
    logger.info("Starting scheduled Morning Brief job...")
    async with AsyncSessionLocal() as db:
        # Get the top 3 recommendations
        stmt = select(Recommendation).order_by(Recommendation.id.desc()).limit(3)
        result = await db.execute(stmt)
        recs = result.scalars().all()
        
        if recs:
            notifier = NotificationService()
            notifier.send_morning_brief(recs)
        else:
            logger.info("No recommendations found to email.")

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # Run every day at 7:00 AM (server time/Bucharest equivalent depending on env)
        # Using simple cron for MVP (Hour=7, Min=0)
        self.scheduler.add_job(
            run_morning_brief_job,
            CronTrigger(hour=7, minute=0),
            id='morning_brief_job',
            name='Send morning brief email',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("APScheduler started. Morning Brief scheduled for 07:00 daily.")
        
    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("APScheduler shut down.")
