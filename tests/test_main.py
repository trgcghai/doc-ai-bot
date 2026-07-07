import json
from pathlib import Path
from main import load_hashes, save_hashes, classify_articles


def test_load_hashes_returns_dict(tmp_path):
    hash_file = tmp_path / ".hashes.json"
    hash_file.write_text('{"slug1": "abc", "slug2": "def"}')
    result = load_hashes(hash_file)
    assert result == {"slug1": "abc", "slug2": "def"}


def test_load_hashes_missing_file_returns_empty(tmp_path):
    hash_file = tmp_path / ".hashes.json"
    result = load_hashes(hash_file)
    assert result == {}


def test_save_hashes_writes_file(tmp_path):
    hash_file = tmp_path / ".hashes.json"
    data = {"slug1": "abc", "slug2": "def"}
    save_hashes(data, hash_file)
    assert hash_file.exists()
    assert json.loads(hash_file.read_text()) == data


def test_classify_articles_all_new():
    old = {}
    new = {"a": "1", "b": "2"}
    added, updated, skipped = classify_articles(old, new)
    assert added == ["a", "b"]
    assert updated == []
    assert skipped == []


def test_classify_articles_mixed():
    old = {"a": "1", "b": "2", "c": "3"}
    new = {"a": "1", "b": "99", "d": "4"}
    added, updated, skipped = classify_articles(old, new)
    assert added == ["d"]
    assert updated == ["b"]
    assert skipped == ["a"]
