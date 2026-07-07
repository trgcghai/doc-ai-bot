import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from scraper import fetch_articles, save_article
from upload_store import _get_client

load_dotenv()


def _require_env(key: str, hint: str = "") -> str:
    value = os.getenv(key)
    if not value:
        msg = f"{key} is required" + (f" ({hint})" if hint else "")
        raise ValueError(msg)
    return value


DATA_DIR = Path(_require_env("DATA_DIR", "directory for markdown files"))
HASHES_PATH = DATA_DIR / ".hashes.json"
VECTOR_STORE_ID = _require_env("VECTOR_STORE_ID", "OpenAI vector store ID, e.g. vs_abc123")


def load_hashes(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_hashes(hashes: dict[str, str], path: Path) -> None:
    path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


def classify_articles(
    old: dict[str, str], new: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    for slug, md5 in new.items():
        if slug not in old:
            added.append(slug)
        elif old[slug] != md5:
            updated.append(slug)
        else:
            skipped.append(slug)
    return added, updated, skipped


def main() -> int:
    old_hashes = load_hashes(HASHES_PATH)

    articles = fetch_articles(min_count=int(_require_env("MIN_ARTICLE_COUNT", "minimum number of articles to fetch (integer)")))
    print(f"Fetched {len(articles)} articles")

    new_hashes: dict[str, str] = {}
    for article in articles:
        slug, md5 = save_article(article, output_dir=str(DATA_DIR))
        new_hashes[slug] = md5
        print(f"  Saved: {slug}.md")

    added, updated, skipped = classify_articles(old_hashes, new_hashes)
    print(f"\nDelta: {len(added)} added, {len(updated)} updated, {len(skipped)} skipped")

    if added or updated:
        client = _get_client()
        for slug in added + updated:
            filepath = DATA_DIR / f"{slug}.md"
            print(f"  Uploading: {filepath.name}")
            with open(filepath, "rb") as f:
                uploaded = client.files.create(file=f, purpose="assistants")
            client.vector_stores.files.create(
                vector_store_id=VECTOR_STORE_ID, file_id=uploaded.id
            )
    else:
        print("  No files to upload")

    save_hashes(new_hashes, HASHES_PATH)
    print(f"\nDone. Hashes saved to {HASHES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
