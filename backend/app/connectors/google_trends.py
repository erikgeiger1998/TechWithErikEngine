from pytrends.request import TrendReq
from app.models.signal import Signal

class GoogleTrendsRomaniaConnector:
    """
    Fetches real-time trending search queries for Romania using Google Trends.
    """
    def __init__(self):
        # hl='ro' (Romanian language), tz=-120 (Eastern European Time UTC+2)
        self.pytrends = TrendReq(hl='ro', tz=-120, timeout=(10,25))
        
    async def discover(self) -> list[str]:
        # There's no specific URL to discover, just the API trigger
        return ["api_call_trends"]
        
    async def fetch(self, url: str) -> dict:
        # Fetch trending searches for Romania
        df = self.pytrends.trending_searches(pn='romania')
        trending_topics = df[0].tolist() # df[0] contains the query strings
        
        return {
            "status_code": 200,
            "trends": trending_topics
        }
        
    async def normalize(self, raw_data: dict) -> list[dict]:
        signals = []
        for index, query in enumerate(raw_data.get("trends", [])):
            # The higher it is on the list (lower index), the higher the importance
            importance = max(100 - (index * 5), 10) # 100 for #1, 95 for #2, etc.
            
            signals.append({
                "source_name": "Google Trends (Romania)",
                "category": "Demand",
                "raw_content": query,
                "reliability": 9.0, # Highly reliable Google data
                "importance": float(importance)
            })
            
        return signals
