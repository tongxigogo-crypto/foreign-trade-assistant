from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .contracts import ActionExecutionResult, CustomerProfile, ProductRecord
from .email_thread_parser import ParsedEmailThread, parse_email_thread_file
from .local_store import LocalKnowledgeStore, slugify_id
from .state_board import StateBoard

SUPPORTED_EMAIL_SUFFIXES = {".txt", ".eml", ".md"}


@dataclass
class EmailImportStats:
    scanned_files: int = 0
    imported_files: int = 0
    skipped_files: int = 0
    extracted_facts: int = 0
    duplicate_skipped: int = 0
    failed_files: list[str] | None = None
    customers_touched: int = 0

    def to_dict(self) -> dict:
        return {
            "scanned_files": self.scanned_files,
            "imported_files": self.imported_files,
            "skipped_files": self.skipped_files,
            "extracted_facts": self.extracted_facts,
            "duplicate_skipped": self.duplicate_skipped,
            "failed_files": self.failed_files or [],
            "customers_touched": self.customers_touched,
        }


def scan_email_thread_files(directory: Path, *, recursive: bool = True, max_files: int = 500) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    out: list[Path] = []
    for path in directory.glob(pattern):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EMAIL_SUFFIXES:
            continue
        out.append(path)
        if len(out) >= max_files:
            break
    return out


def ingest_email_thread_directory(
    *,
    store: LocalKnowledgeStore,
    state_board: StateBoard,
    directory: Path,
    recursive: bool = True,
    max_files: int = 500,
    progress_callback: Callable[[dict], None] | None = None,
    source_files: list[Path] | None = None,
) -> EmailImportStats:
    stats = EmailImportStats(failed_files=[])
    files = source_files or scan_email_thread_files(directory, recursive=recursive, max_files=max_files)
    stats.scanned_files = len(files)
    total = len(files)
    existing_facts = set(store.load().doc_facts)
    touched_customers: set[str] = set()
    for idx, path in enumerate(files, start=1):
        try:
            parsed = parse_email_thread_file(path)
        except OSError:
            stats.failed_files.append(str(path))
            if progress_callback:
                progress_callback(_progress_payload(stats, idx, total, path))
            continue
        if not _is_meaningful(parsed):
            stats.skipped_files += 1
            if progress_callback:
                progress_callback(_progress_payload(stats, idx, total, path))
            continue
        customer_id, customer_name = _upsert_customer_from_parsed(store=store, parsed=parsed)
        touched_customers.add(customer_id)
        _ensure_products(store=store, products=parsed.products)
        stats.extracted_facts += _append_unique_facts(store=store, facts=parsed.summary_facts, existing_facts=existing_facts, stats=stats)
        ingest_result = ActionExecutionResult(
            status="success",
            message=f"Ingested email thread for {customer_name}; detected {len(parsed.products)} products.",
            artifacts=[str(store.knowledge_file)],
            context={"customer_id": customer_id, "customer_name": customer_name, "source_file": str(path)},
        )
        event = state_board.append_execution(action_name="ingest_email_thread", results=[ingest_result])
        state_board.transition_customer_tasks(
            customer_id=customer_id,
            to_status="in_progress",
            note="Auto-progressed by new inbound email reply detection.",
            from_statuses=("waiting_reply", "overdue"),
            max_items=2,
        )
        state_board.create_followup_task(
            customer_id=customer_id,
            customer_name=customer_name,
            title=f"Follow up inquiry thread for {customer_name}",
            due_in_days=3,
            priority="high" if parsed.issues else "normal",
            source_event_id=event["event_id"],
            initial_status="in_progress",
        )
        stats.imported_files += 1
        if progress_callback:
            progress_callback(_progress_payload(stats, idx, total, path))
    stats.customers_touched = len(touched_customers)
    return stats


def _is_meaningful(parsed: ParsedEmailThread) -> bool:
    return bool(
        parsed.customer_name
        or parsed.customer_email
        or parsed.customer_phone
        or parsed.products
        or parsed.trade_terms
        or parsed.summary_facts
    )


def _upsert_customer_from_parsed(*, store: LocalKnowledgeStore, parsed: ParsedEmailThread) -> tuple[str, str]:
    customer_name = parsed.customer_name.strip() or "Unknown Customer"
    customer_id = slugify_id(customer_name)
    existing = store.find_customer(customer_id)
    customer = existing or CustomerProfile(customer_id=customer_id, name=customer_name)
    customer.name = customer_name or customer.name
    customer.region = parsed.country_or_region or customer.region
    if parsed.customer_email and f"Email: {parsed.customer_email}" not in customer.notes:
        customer.notes.append(f"Email: {parsed.customer_email}")
    if parsed.customer_phone and f"Phone: {parsed.customer_phone}" not in customer.notes:
        customer.notes.append(f"Phone: {parsed.customer_phone}")
    for issue in parsed.issues:
        if issue not in customer.last_issues:
            customer.last_issues.append(issue)
    for tag in ["email_thread_ingested"] + parsed.trade_terms:
        if tag and tag not in customer.tags:
            customer.tags.append(tag)
    store.upsert_customer(customer)
    return customer.customer_id, customer.name


def _ensure_products(*, store: LocalKnowledgeStore, products: list[str]) -> None:
    for sku in products:
        if not store.find_product(sku):
            store.upsert_product(ProductRecord(sku=sku, name=sku))


def _append_unique_facts(*, store: LocalKnowledgeStore, facts: list[str], existing_facts: set[str], stats: EmailImportStats) -> int:
    new_items: list[str] = []
    for fact in facts:
        normalized = str(fact).strip()
        if not normalized:
            continue
        if normalized in existing_facts:
            stats.duplicate_skipped += 1
            continue
        existing_facts.add(normalized)
        new_items.append(normalized)
    if new_items:
        store.append_doc_facts(new_items)
    return len(new_items)


def _progress_payload(stats: EmailImportStats, current: int, total: int, path: Path) -> dict:
    return {
        "current": current,
        "total": total,
        "path": str(path),
        "imported_files": stats.imported_files,
        "skipped_files": stats.skipped_files,
        "facts": stats.extracted_facts,
        "failed_files": len(stats.failed_files or []),
    }
