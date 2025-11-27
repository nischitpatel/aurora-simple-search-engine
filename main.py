from fastapi import FastAPI, HTTPException
import httpx
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

EXTERNAL_API = os.getenv("BASE_URL")

app = FastAPI(title="Simple Search Engine")

# Global cache storage
cache = None

# Background cache loader
async def cache_loader():
    global cache
    cache = []
    skip = 0
    limit = 200

    async with httpx.AsyncClient() as client:
        while True:
            try:
                r = await client.get(EXTERNAL_API, params={"skip": skip, "limit": limit})
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    print("Reached the end of available messages.")
                    break
                else:
                    print("Failed to load cache:", e)
                    break

            data = r.json()
            if not data["items"]:
                break

            cache.extend(data["items"])
            skip += limit

    print(f"Loaded {len(cache)} messages.")


@app.on_event("startup")
async def load_cache():
    asyncio.create_task(cache_loader())

# Lazy fallback loader
async def cached_messages():
    global cache
    if cache is None:
        print("Cache not ready — loading on demand...")
        await cache_loader()

    # return cache.get("items", [])
    return cache

# Search API
@app.get("/search")
async def search(query: str, page: int = 1, page_size: int = 20):

    if page < 1 or page_size < 1:
        raise HTTPException(status_code=422, detail="page and page_size must be >= 1")

    messages = await cached_messages()

    query_lower = query.lower()

    matched = [
        msg for msg in messages
        if query_lower in msg.get("message", "").lower()
    ]

    total = len(matched)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "query": query,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": matched[start:end]
    }
