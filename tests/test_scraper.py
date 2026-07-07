import pytest
from scraper import fetch_articles, save_article


def test_fetch_articles_returns_30_articles():
    articles = fetch_articles(min_count=30)
    assert len(articles) >= 30


def test_fetch_articles_has_required_fields():
    articles = fetch_articles(min_count=1)
    for a in articles:
        assert "title" in a
        assert "slug" in a
        assert "body" in a
        assert "id" in a


def test_save_article_creates_md_file(tmp_path):
    article = {
        "title": "Test Article",
        "slug": "test-article",
        "body": "<h1>Hello</h1><p>World</p>",
        "id": "999999",
    }
    slug, md5 = save_article(article, output_dir=str(tmp_path))
    file_path = tmp_path / f"{slug}.md"
    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    assert "Hello" in content
    assert "Article URL:" in content
    assert "999999" in content


def test_save_article_sanitizes_slug(tmp_path):
    article = {
        "title": "Bad Slug",
        "slug": "../../malicious",
        "body": "<p>test</p>",
        "id": "1",
    }
    slug, _ = save_article(article, output_dir=str(tmp_path))
    assert "/" not in slug
    assert "\\" not in slug
