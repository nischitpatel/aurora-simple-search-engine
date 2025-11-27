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
    print("Loading cache...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(EXTERNAL_API, params={"skip": 0, "limit": 200})
            r.raise_for_status()
            cache = r.json()
            print("Cache loaded successfully.")

    except Exception as e:
        print("Failed to load cache:", e)
        cache = {"items": []}  # fallback


@app.on_event("startup")
async def load_cache():
    asyncio.create_task(cache_loader())

# Lazy fallback loader
async def cached_messages():
    global cache
    if cache is None:
        print("Cache not ready — loading on demand...")
        await cache_loader()

    return cache.get("items", [])

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
