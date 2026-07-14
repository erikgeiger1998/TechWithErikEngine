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
        # We define seed keywords for the Romanian tech market
        return ["telefon", "laptop", "iphone", "samsung", "emag", "altex", "aplicatie", "windows"]
        
    async def fetch(self, url: str) -> dict:
        # Here 'url' is our keyword
        keyword = url
        try:
            # Build payload for Romania in the last 7 days
            self.pytrends.build_payload(kw_list=[keyword], geo='RO', timeframe='now 7-d')
            # Get related queries
            queries = self.pytrends.related_queries()
            
            trending_topics = []
            if keyword in queries and queries[keyword] and queries[keyword]['rising'] is not None:
                df = queries[keyword]['rising']
                trending_topics = df['query'].tolist()
                
            return {
                "status_code": 200,
                "keyword": keyword,
                "trends": trending_topics
            }
        except Exception as e:
            # If Google rate limits or fails, return empty gracefully
            return {
                "status_code": 404, # Signal warning in pipeline
                "keyword": keyword,
                "trends": []
            }
        
    async def normalize(self, raw_data: dict) -> list[dict]:
        signals = []
        keyword = raw_data.get("keyword", "")
        
        for index, query in enumerate(raw_data.get("trends", [])):
            # The higher it is on the rising list (lower index), the higher the importance
            importance = max(100 - (index * 5), 10) # 100 for #1, 95 for #2, etc.
            
            signals.append({
                "source_name": f"Google Trends RO ({keyword})",
                "category": "Demand",
                "raw_content": query,
                "reliability": 9.0, # Highly reliable Google data
                "importance": float(importance)
            })
            
        return signals
