from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CRM_STORE = DATA_DIR / "crm_store.json"
PRICING_RULES = DATA_DIR / "pricing_rules.json"
