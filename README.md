# Aurora - Search Engine

**Super-fast keyword search API built with FastAPI** – serves queries in **<70ms** using an **in-memory inverted index** with periodic cache refresh.

---

### **Tech Stack**

* Python 3.11+, FastAPI, httpx, asyncio
* `collections.defaultdict` for inverted index

---

### **Quick Start**

1. Clone repo and create virtual environment

```bash
git clone https://github.com/nischitpatel/aurora-simple-search-engine.git
cd aurora-simple-search-engine
python -m venv venv
source venv/Scripts/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set `.env` with your API endpoint

```
BASE_URL=https://example.com/api/messages
```

4. Run server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

5. Search

```
GET /search?query=keyword&page=1&page_size=20
```

---

#### **Design Notes**

Several alternative approaches were considered for building this search engine:

1. **Database-based search (SQL/NoSQL)**

   * Using PostgreSQL full-text search or MongoDB text indexes.
   * Pros: Persistence, built-in query support.
   * Cons: Higher latency (50–200ms), slower than in-memory search.

2. **Elasticsearch / OpenSearch**

   * Pros: Advanced search features (ranking, fuzzy search, filtering).
   * Cons: Adds infrastructure complexity, memory overhead, slower for small datasets.
   *we can add this if the dataset is very large*

3. **Caching layers (Redis / Memcached)**

   * Store frequently searched queries or index in Redis.
   * Pros: Ultra-low latency, scalable across multiple instances.
   * Cons: Adds external dependency, cache invalidation needed.

---

#### **Data Insights – Reducing Latency to 30ms**

To further reduce search latency from 50ms → 30ms:

1. **Use Redis for the inverted index**

   * Store word -> list of IDs in Redis, which is extremely fast (<1ms lookup).

2. **Precompute query results for popular searches**

   * Maintain a small cache for hot keywords.

3. **Optimize Python data structures**

   * We can use sets instead of lists to store message IDs for faster deduplication.

4. **Parallelize index rebuilding**

   * For very large datasets, we can use `asyncio.gather` or multiprocessing to build index faster.

---

**Author:** Nischit Patel
**LinkedIn:** [linkedin.com/in/nischit-patel](https://www.linkedin.com/in/nischit-patel)
