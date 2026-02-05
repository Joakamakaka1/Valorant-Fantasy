"""
Image proxy endpoint to bypass hotlink protection from external sources like Liquipedia.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["Proxy"])


@router.get("/image")
async def proxy_image(url: str):
    """
    Proxy external images to bypass hotlink protection.
    
    Example: /api/v1/proxy/image?url=https://liquipedia.net/commons/images/.../player.jpg
    """
    # Validate URL is from allowed sources
    allowed_domains = ["liquipedia.net"]
    
    if not any(domain in url for domain in allowed_domains):
        raise HTTPException(
            status_code=400,
            detail="URL not from allowed domain"
        )
    
    try:
        # Fetch image with proper headers to bypass hotlink protection
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://liquipedia.net/",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                },
                follow_redirects=True
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch image from {url}: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch image: {response.status_code}"
                )
            
            # Return image with proper content type
            return StreamingResponse(
                iter([response.content]),
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                }
            )
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching image: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching image: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
