import pytest
from upload_store import upload_to_store


def test_upload_store_returns_string():
    store_id = upload_to_store()
    assert isinstance(store_id, str)
    assert store_id.startswith("vs_")
