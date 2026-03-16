from pathlib import Path
from app.data_access.crm_store import load_store, save_store


def test_crm_store_roundtrip(tmp_path: Path):
    path = tmp_path / "crm.json"
    data = {"customers": [{"email": "a@example.com"}]}
    save_store(path, data)
    loaded = load_store(path)
    assert loaded["customers"][0]["email"] == "a@example.com"
