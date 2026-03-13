"""Central configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]


@dataclass(slots=True)
class Settings:
    app_env: str
    log_level: str
    log_path: Path
    crm_store_path: Path
    pricing_rules_path: Path
    freight_rules_path: Path
    compliance_rules_path: Path
    retry_max_attempts: int
    retry_base_delay_seconds: float


def load_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv()
    return Settings(
        app_env=getenv("APP_ENV", "development"),
        log_level=getenv("LOG_LEVEL", "INFO"),
        log_path=Path(getenv("LOG_PATH", "logs/system.log")),
        crm_store_path=Path(getenv("CRM_STORE_PATH", "data/crm_store.json")),
        pricing_rules_path=Path(getenv("PRICING_RULES_PATH", "data/pricing_rules.json")),
        freight_rules_path=Path(getenv("FREIGHT_RULES_PATH", "data/freight_rules.json")),
        compliance_rules_path=Path(getenv("COMPLIANCE_RULES_PATH", "data/compliance_rules.json")),
        retry_max_attempts=int(getenv("RETRY_MAX_ATTEMPTS", "3")),
        retry_base_delay_seconds=float(getenv("RETRY_BASE_DELAY_SECONDS", "0.2")),
    )
