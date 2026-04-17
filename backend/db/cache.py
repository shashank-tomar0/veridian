import json
from redis.asyncio import Redis
from backend.config import settings

class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def cache_analysis_result(self, file_hash: str, result: dict, ttl: int = 259200):
        await self.redis.set(f"analysis:{file_hash}", json.dumps(result), ex=ttl)

    async def get_cached_result(self, file_hash: str) -> dict | None:
        data = await self.redis.get(f"analysis:{file_hash}")
        if data:
            return json.loads(data)
        return None

    async def rate_limit_check(self, user_id: str, tier: str) -> bool:
        # Implement sliding window algorithm
        limits = {"read": 100, "analyze": 10, "admin": 1000}
        limit = limits.get(tier, 10)
        
        key = f"rate_limit:{user_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60) # 1 minute window
        
        if current > limit:
            return False
        return True

    async def close(self):
        await self.redis.aclose()

cache_service = CacheService()
