import httpx
from bs4 import BeautifulSoup
from datetime import datetime

class ChannelConnector:
    """
    Automatically fetches recent published videos from a public YouTube RSS feed.
    Zero OAuth required. Captures basic performance metrics (views).
    """
    # Dummy channel ID for MVP. In reality, Erik will provide his channel ID here.
    CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw" # Google Developers for placeholder
    FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

    @classmethod
    async def fetch(cls) -> list[dict]:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(cls.FEED_URL)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            entries = soup.find_all("entry")
            
            videos = []
            for entry in entries:
                video_id = entry.find("yt:videoId").text if entry.find("yt:videoId") else None
                title = entry.find("title").text if entry.find("title") else "Unknown"
                link = entry.find("link")["href"] if entry.find("link") else None
                
                # YouTube RSS includes views in media:statistics
                stats = entry.find("media:statistics")
                views = int(stats["views"]) if stats and stats.has_attr("views") else 0
                
                # Published Date
                pub_date_str = entry.find("published").text if entry.find("published") else None
                published_at = datetime.fromisoformat(pub_date_str) if pub_date_str else None
                
                if link and title:
                    videos.append({
                        "video_id": video_id,
                        "title": title,
                        "url": link,
                        "views": views,
                        "published_at": published_at,
                        "likes": 0 # Not exposed in RSS, but structure is ready for it
                    })
                    
            return videos
