import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal
from app.models.source_profile import SourceProfile, ConnectorType


sources = [
    {
        "name": "Apple Newsroom",
        "connector_type": ConnectorType.OFFICIAL,
        "reliability": 100,
        "importance": 90,
        "romanian_relevance": 50,
        "is_official": True,
        "update_frequency": "15m",
        "expected_latency": "low",
        "category": "apple_news",
        "language": "en",
        "api_available": False,
        "rate_limits": "RSS"
    },
    {
        "name": "Apple Support",
        "connector_type": ConnectorType.OFFICIAL,
        "reliability": 100,
        "importance": 100,
        "romanian_relevance": 80,
        "is_official": True,
        "update_frequency": "120m",
        "expected_latency": "medium",
        "category": "support",
        "language": "en",
        "api_available": False,
        "rate_limits": "HTML"
    },
    {
        "name": "DNSC Romania",
        "connector_type": ConnectorType.OFFICIAL,
        "reliability": 99,
        "importance": 100,
        "romanian_relevance": 100,
        "is_official": True,
        "update_frequency": "30m",
        "expected_latency": "medium",
        "category": "cybersecurity",
        "language": "ro",
        "api_available": False,
        "rate_limits": "RSS/HTML"
    },
    {
        "name": "Google Trends Romania",
        "connector_type": ConnectorType.TREND,
        "reliability": 0,
        "importance": 95,
        "romanian_relevance": 100,
        "is_official": True,
        "update_frequency": "1h",
        "expected_latency": "low",
        "category": "search_demand",
        "language": "ro",
        "api_available": False,
        "rate_limits": "RSS"
    },
    {
        "name": "Google Autocomplete Romania",
        "connector_type": ConnectorType.TREND,
        "reliability": 0,
        "importance": 90,
        "romanian_relevance": 100,
        "is_official": False,
        "update_frequency": "daily",
        "expected_latency": "low",
        "category": "human_friction",
        "language": "ro",
        "api_available": False,
        "rate_limits": "Suggest API"
    },
    {
        "name": "Reddit Tech Communities",
        "connector_type": ConnectorType.COMMUNITY,
        "reliability": 40,
        "importance": 75,
        "romanian_relevance": 40,
        "is_official": False,
        "update_frequency": "15m",
        "expected_latency": "low",
        "category": "complaints",
        "language": "en",
        "api_available": True,
        "rate_limits": "API"
    }
]


async def seed():
    async with AsyncSessionLocal() as session:

        for source in sources:

            existing = await session.execute(
                SourceProfile.__table__.select()
                .where(SourceProfile.name == source["name"])
            )

            if existing.first():
                print(f"SKIP {source['name']}")
                continue

            profile = SourceProfile(**source)
            session.add(profile)

            print(f"ADD {source['name']}")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
