# OptiBot Mini-Clone

Ingests OptiSigns support articles, uploads them to an OpenAI vector store, and runs every 2 hours to keep them fresh.

## Setup

```bash
cp .env.sample .env
# Fill in OPENAI_API_KEY, ZENDESK_BASE_URL, VECTOR_STORE_ID, VECTOR_STORE_NAME, DATA_DIR, MIN_ARTICLE_COUNT
pip install -r requirements.txt
```

## Usage

### One-time: scrape + upload

```bash
python scraper.py          # saves .md files to DATA_DIR
python upload_store.py     # uploads all .md files to OpenAI vector store
```

### Daily job (delta)

```bash
python main.py             # rescrapes, detects new/updated files, uploads delta
```

Logic: `data/.hashes.json` stores slug → md5_hash per run. Only new/changed files are uploaded.

### Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t optibot .
docker run --env-file .env optibot
```

## Chunking Strategy

OpenAI's default (`max_chunk_size_tokens=800`) is used for each file. One markdown file per article keeps context clean.

## Deployment

**Platform:** Railway  
**Schedule:** `0 */2 * * *` (every 2 hours)  
**Cron Logs:** https://railway.com/project/.../cron  

The `railway.toml` cron triggers `main.py` on schedule. Each run prints delta counts (added / updated / skipped) and uploads only changed files to the OpenAI vector store. Container exits with code 0 on success; failures appear in deployment logs.

## Screenshot

![Assistant answering "How do I add a YouTube video?"](screenshot.png)

The assistant correctly cites article URLs in its response.
