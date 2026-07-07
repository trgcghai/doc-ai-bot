import hashlib
import os
import re
import sys
from pathlib import Path

import html2text
import requests
from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str, hint: str = "") -> str:
    value = os.getenv(key)
    if not value:
        msg = f"{key} is required" + (f" ({hint})" if hint else "")
        raise ValueError(msg)
    return value


ZENDESK_BASE = _require_env("ZENDESK_BASE_URL", "Zendesk help center base URL, e.g. https://support.example.com")
ARTICLES_URL = f"{ZENDESK_BASE}/api/v2/help_center/articles"


def fetch_articles(min_count: int = 30) -> list[dict]:
    params = {"per_page": min_count}
    resp = requests.get(ARTICLES_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    raw_articles = data.get("articles", [])
    if len(raw_articles) < min_count:
        print(
            f"Warning: got {len(raw_articles)} articles, requested {min_count}",
            file=sys.stderr,
        )
    result = []
    for a in raw_articles:
        article_id = a["id"]
        url_part = a["html_url"].rsplit("/", 1)[-1]
        slug = url_part.split("-", 1)[-1] if "-" in url_part else str(article_id)
        result.append({
            "id": article_id,
            "title": a["title"],
            "slug": slug,
            "body": a.get("body", ""),
        })
    return result


def _sanitize_slug(slug: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', slug)
    return sanitized[:100] or "article"


def _rewrite_links(html: str, base_url: str) -> str:
    def replace_href(match):
        url = match.group(1)
        if url.startswith("/"):
            url = base_url + url
        return f'href="{url}"'

    def replace_src(match):
        url = match.group(1)
        if url.startswith("/"):
            url = base_url + url
        return f'src="{url}"'

    html = re.sub(r'href="([^"]+)"', replace_href, html)
    html = re.sub(r'src="([^"]+)"', replace_src, html)
    return html


def save_article(article: dict, output_dir: str = "data") -> tuple[str, str]:
    slug = _sanitize_slug(article["slug"])
    body_html = article.get("body", "")

    body_html = _rewrite_links(body_html, ZENDESK_BASE)

    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    converter.ignore_images = False
    converter.mark_code = True
    markdown = converter.handle(body_html).strip()

    article_url = f"{ZENDESK_BASE}/hc/en-us/articles/{article['id']}"
    markdown += f"\n\nArticle URL: {article_url}"

    os.makedirs(output_dir, exist_ok=True)
    filepath = Path(output_dir) / f"{slug}.md"
    filepath.write_text(markdown, encoding="utf-8")

    md5_hash = hashlib.md5(markdown.encode("utf-8")).hexdigest()
    return slug, md5_hash


def main():
    articles = fetch_articles(min_count=30)
    print(f"Fetched {len(articles)} articles")

    results = []
    for article in articles:
        slug, md5 = save_article(article)
        results.append((slug, md5))
        print(f"  Saved: {slug}.md")

    print(f"\nDone. {len(results)} files written to data/")


if __name__ == "__main__":
    main()
