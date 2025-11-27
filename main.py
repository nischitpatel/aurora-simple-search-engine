from fastapi import FastAPI, HTTPException
import httpx
import asyncio
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

EXTERNAL_API = os.getenv("BASE_URL")
if not EXTERNAL_API:
    raise RuntimeError("BASE_URL environment variable not set.")

app = FastAPI(title="Ultra-Fast Search Engine (Inverted Index)")

# GLOBAL STORAGE
messages_store = {}          # msg_id - message dict
inverted_index = defaultdict(list)   # word - list of msg_ids


# HELPER FUNCTION: Build inverted index
def build_inverted_index(messages):
    """
    Builds an inverted index for O(1) keyword lookups.
    """
    for msg in messages:
        msg_id = msg["id"]
        messages_store[msg_id] = msg

        # Simple tokenization
        words = msg["message"].lower().split()

        for w in words:
            inverted_index[w].append(msg_id)

    print(f"Inverted index built with {len(inverted_index)} unique words.")


# Loader: Fetch ALL messages before server starts
async def fetch_all_messages():
    """
    Pulls all messages from external API using pagination until no more data.
    """
    all_messages = []
    skip = 0
    limit = 1000

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            url = EXTERNAL_API
            try:
                resp = await client.get(method="GET", url=url, params={"skip": skip, "limit": limit})
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # 400 means "no more pages"
                if e.response.status_code == 400:
                    print("Reached the end of dataset.")
                    break
                raise RuntimeError(f"API error: {e}") from e

            data = resp.json()

            if not data["items"]:
                break

            all_messages.extend(data["items"])
            skip += limit

    print(f"Loaded {len(all_messages)} messages from external API.")
    return all_messages

# Startup event — LOAD EVERYTHING BEFORE SERVER STARTS
@app.on_event("startup")
async def startup_event():
    print("\n=== LOADING DATA BEFORE SERVER START ===")
    all_messages = await fetch_all_messages()
    build_inverted_index(all_messages)
    print("Server ready!\n")

# SEARCH ENDPOINT
@app.get("/search")
async def search(query: str, page: int = 1, page_size: int = 20):
    """
    Search using inverted index.
    """
    if page < 1 or page_size < 1:
        raise HTTPException(422, detail="page and page_size must be >= 1")

    query_words = query.lower().split()

    # Collect matching message IDs for each word
    result_ids = []
    for q in query_words:
        result_ids.extend(inverted_index.get(q, []))

    # Deduplicate
    result_ids = list(set(result_ids))

    # Convert IDs - message dicts
    results = [messages_store[mid] for mid in result_ids]

    # Pagination
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "query": query,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": results[start:end]
    }