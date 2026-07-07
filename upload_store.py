import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def _require_env(key: str, hint: str = "") -> str:
    value = os.getenv(key)
    if not value:
        msg = f"{key} is required" + (f" ({hint})" if hint else "")
        raise ValueError(msg)
    return value


DATA_DIR = Path(_require_env("DATA_DIR", "directory for markdown files"))
STORE_NAME = _require_env("VECTOR_STORE_NAME", "name for the OpenAI vector store")


def _get_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .env")
    return OpenAI(api_key=api_key)


def _get_or_create_vector_store(client: OpenAI) -> str:
    stores = client.vector_stores.list()
    for store in stores:
        if store.name == STORE_NAME:
            logger.info("Found existing store: %s (%s)", store.name, store.id)
            return store.id
    store = client.vector_stores.create(name=STORE_NAME)
    logger.info("Created store: %s (%s)", store.name, store.id)
    return store.id


def upload_to_store(store_id: str | None = None) -> str:
    client = _get_client()
    if store_id is None:
        store_id = _get_or_create_vector_store(client)

    md_files = sorted(DATA_DIR.glob("*.md"))
    if not md_files:
        logger.warning("No .md files found in %s", DATA_DIR)
        return store_id

    total_bytes = 0
    for i, filepath in enumerate(md_files, 1):
        logger.info("Uploading %d/%d: %s", i, len(md_files), filepath.name)
        with open(filepath, "rb") as f:
            uploaded = client.files.create(file=f, purpose="assistants")
        client.vector_stores.files.create(
            vector_store_id=store_id, file_id=uploaded.id
        )
        total_bytes += filepath.stat().st_size

    vs = client.vector_stores.retrieve(store_id)
    logger.info("Uploaded %d files, %d chunks embedded", len(md_files), vs.file_counts.total)
    logger.info("Store: %s (%s)", vs.name, vs.id)
    logger.info("Total size: %s bytes", total_bytes)
    return store_id


if __name__ == "__main__":
    result = upload_to_store()
    print(f"Store ID: {result}")
