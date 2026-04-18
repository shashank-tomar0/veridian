import trafilatura
import httpx
import structlog
from typing import Optional, Dict, Any

logger = structlog.get_logger()

class ScraperService:
    """Service for extracting clean article text from news URLs."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Veridian/1.0"}
        )

    async def extract(self, url: str) -> Dict[str, Any]:
        """Fetch and extract article content, title, and metadata."""
        try:
            logger.info("scraper.fetch_start", url=url)
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Extract main content
            downloaded = trafilatura.extract(
                html, 
                include_comments=False,
                include_tables=True,
                output_format="txt",
                favor_recall=True
            )
            
            # Extract metadata (title, etc)
            metadata = trafilatura.extract_metadata(html)
            
            if not downloaded:
                logger.warning("scraper.no_content", url=url)
                return {
                    "success": False,
                    "error": "Could not extract body text from this URL.",
                    "title": metadata.title if metadata else "Unknown Page"
                }

            return {
                "success": True,
                "text": downloaded,
                "title": metadata.title if metadata else "Unknown Page",
                "author": metadata.author if metadata else "Unknown",
                "date": metadata.date if metadata else None,
                "url": url
            }

        except Exception as e:
            logger.error("scraper.error", url=url, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

scraper_service = ScraperService()
