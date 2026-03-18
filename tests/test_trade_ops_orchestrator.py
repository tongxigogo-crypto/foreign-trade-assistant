import csv
import json
import tempfile
import unittest
from pathlib import Path

from trade_ops.orchestrator import OrchestratorConfig, run_orchestration


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TradeOpsOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        _write_json(
            self.root / "trade_ops" / "config" / "pricing-rules.json",
            {"fallbackUnitPrice": 5.5, "defaultCurrency": "USD", "shippingPerOrder": 90},
        )
        _write_json(
            self.root / "trade_ops" / "state.json",
            {"mic_last_index": 0},
        )
        _write_csv(
            self.root / "trade_ops" / "input" / "inquiries.csv",
            [
                "inquiry_id",
                "company_name",
                "contact_name",
                "product_name",
                "request_qty",
                "base_unit_price",
                "inquiry_message",
            ],
            [
                {
                    "inquiry_id": "INQ-1",
                    "company_name": "Acme",
                    "contact_name": "Eve",
                    "product_name": "Valve",
                    "request_qty": "100",
                    "base_unit_price": "",
                    "inquiry_message": "Need quote",
                }
            ],
        )
        _write_csv(
            self.root / "trade_ops" / "input" / "mic-products.csv",
            ["product_id", "product_name", "mic_url", "target_market", "owner"],
            [
                {
                    "product_id": "P1",
                    "product_name": "Valve",
                    "mic_url": "https://example.com/p1",
                    "target_market": "US",
                    "owner": "Amy",
                }
            ],
        )
        _write_csv(
            self.root / "trade_ops" / "input" / "site-pages.csv",
            ["page_slug", "page_url", "seo_keyword", "needs_content", "needs_image", "priority"],
            [
                {
                    "page_slug": "home",
                    "page_url": "https://example.com",
                    "seo_keyword": "keyword",
                    "needs_content": "1",
                    "needs_image": "0",
                    "priority": "high",
                }
            ],
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_preview_mode_does_not_write_outputs(self) -> None:
        report = run_orchestration(
            OrchestratorConfig(
                root_dir=self.root,
                run_date="2026-03-18",
                confirm_writes=False,
                run_id="run-preview",
            )
        )
        self.assertEqual(report["status"], "needs_confirmation")
        self.assertFalse((self.root / "trade_ops" / "output" / "run-summary-2026-03-18.md").exists())

    def test_confirm_write_persists_outputs_and_state(self) -> None:
        report = run_orchestration(
            OrchestratorConfig(
                root_dir=self.root,
                run_date="2026-03-18",
                confirm_writes=True,
                run_id="run-confirm",
            )
        )
        self.assertEqual(report["status"], "done")
        self.assertTrue((self.root / "trade_ops" / "output" / "run-summary-2026-03-18.md").exists())

        state = json.loads((self.root / "trade_ops" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["workflow"]["status"], "done")
        self.assertEqual(state["workflow"]["last_run_id"], "run-confirm")

    def test_quotation_uses_fallback_price(self) -> None:
        report = run_orchestration(
            OrchestratorConfig(
                root_dir=self.root,
                run_date="2026-03-18",
                confirm_writes=False,
                run_id="run-pricing",
            )
        )
        quotes = next(item for item in report["agent_results"] if item["agent"] == "quotation_agent")["payload"][
            "quotes"
        ]
        self.assertEqual(quotes[0]["unit_price"], 5.5)


if __name__ == "__main__":
    unittest.main()
