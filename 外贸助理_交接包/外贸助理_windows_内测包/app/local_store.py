from __future__ import annotations

import json
import re
import time
from dataclasses import fields
from pathlib import Path

from .contracts import CustomerProfile, KnowledgeBase, ProductRecord, UserPreference

NOISE_EXACT = {
    "user request:",
    "user request: @",
    "追问",
    "复制",
    "快速",
    "@",
}

NOISE_CONTAINS = [
    "[local_context_begin]",
    "[local_context_end]",
    "target model:",
    "instruction:",
    "用户请求:",
    "已知信息:",
    "关键事实",
    "最终注入 prompt",
]

BUSINESS_HINTS = [
    "customer",
    "client",
    "quote",
    "price",
    "product",
    "sku",
    "currency",
    "email",
    "phone",
    "follow-up",
    "payment",
    "onboarding",
    "trade",
    "fob",
    "cif",
    "port",
    "客户",
    "报价",
    "产品",
    "付款",
    "跟进",
    "币种",
    "邮箱",
    "电话",
    "港口",
]


class LocalKnowledgeStore:
    def __init__(self, knowledge_file: Path) -> None:
        self.knowledge_file = knowledge_file

    def ensure_initialized(self) -> None:
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.knowledge_file.exists():
            self.save(KnowledgeBase())

    def load(self) -> KnowledgeBase:
        self.ensure_initialized()
        raw = self.knowledge_file.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            backup_path = self.knowledge_file.with_suffix(self.knowledge_file.suffix + ".corrupt")
            self.knowledge_file.replace(backup_path)
            self.save(KnowledgeBase())
            data = json.loads(self.knowledge_file.read_text(encoding="utf-8"))
        customer_keys = {f.name for f in fields(CustomerProfile)}
        product_keys = {f.name for f in fields(ProductRecord)}
        preference_keys = {f.name for f in fields(UserPreference)}

        customers = {}
        for key, value in data.get("customers", {}).items():
            safe = {k: v for k, v in (value or {}).items() if k in customer_keys}
            customers[key] = CustomerProfile(**safe)

        products = {}
        for key, value in data.get("products", {}).items():
            safe = {k: v for k, v in (value or {}).items() if k in product_keys}
            products[key] = ProductRecord(**safe)

        pref_raw = data.get("preference", {}) or {}
        safe_pref = {k: v for k, v in pref_raw.items() if k in preference_keys}
        preference = UserPreference(**safe_pref)
        return KnowledgeBase(
            customers=customers,
            products=products,
            preference=preference,
            global_facts=list(data.get("global_facts", [])),
            doc_facts=list(data.get("doc_facts", [])),
        )

    def save(self, kb: KnowledgeBase) -> None:
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(kb.to_dict(), ensure_ascii=False, indent=2) + "\n"
        for attempt in range(5):
            temp_path = self.knowledge_file.with_suffix(self.knowledge_file.suffix + f".tmp{attempt}")
            try:
                temp_path.write_text(payload, encoding="utf-8")
                temp_path.replace(self.knowledge_file)
                return
            except PermissionError:
                time.sleep(0.08 * (attempt + 1))
            finally:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
        self.knowledge_file.write_text(payload, encoding="utf-8")

    def upsert_customer(self, customer: CustomerProfile) -> KnowledgeBase:
        kb = self.load()
        kb.customers[customer.customer_id] = customer
        self.save(kb)
        return kb

    def upsert_product(self, product: ProductRecord) -> KnowledgeBase:
        kb = self.load()
        kb.products[product.sku] = product
        self.save(kb)
        return kb

    def update_preference(self, preference: UserPreference) -> KnowledgeBase:
        kb = self.load()
        kb.preference = preference
        self.save(kb)
        return kb

    def append_global_fact(self, fact: str) -> KnowledgeBase:
        kb = self.load()
        value = fact.strip()
        if value and value not in kb.global_facts:
            kb.global_facts.append(value)
        self.save(kb)
        return kb

    def append_doc_facts(self, facts: list[str], max_items: int = 1000) -> KnowledgeBase:
        kb = self.load()
        for fact in facts:
            normalized = fact.strip()
            if normalized and normalized not in kb.doc_facts:
                kb.doc_facts.append(normalized)
        if len(kb.doc_facts) > max_items:
            kb.doc_facts = kb.doc_facts[-max_items:]
        self.save(kb)
        return kb

    def append_conversation_snapshot(self, model_name: str, reply_text: str, max_items: int = 1500) -> KnowledgeBase:
        lines = extract_facts_from_conversation_text(reply_text, max_lines=40, max_chars=240)
        if not lines:
            return self.load()
        tagged = [f"[{model_name}] {line}" for line in lines]
        return self.append_doc_facts(tagged, max_items=max_items)

    def find_customer(self, hint: str, kb: KnowledgeBase | None = None) -> CustomerProfile | None:
        source = kb or self.load()
        needle = hint.strip().lower()
        if not needle:
            return None
        for customer in source.customers.values():
            haystack = " ".join([customer.customer_id, customer.name, customer.region]).lower()
            if needle in haystack:
                return customer
        return None

    def find_product(self, hint: str, kb: KnowledgeBase | None = None) -> ProductRecord | None:
        source = kb or self.load()
        needle = hint.strip().lower()
        if not needle:
            return None
        for product in source.products.values():
            haystack = " ".join([product.sku, product.name]).lower()
            if needle in haystack:
                return product
        return None


def extract_facts_from_text_file(path: Path, max_lines: int = 50) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:max_lines]


def extract_facts_from_conversation_text(text: str, max_lines: int = 40, max_chars: int = 240) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        if not line:
            continue
        if line.startswith("[LOCAL_CONTEXT_BEGIN]") or line.startswith("[LOCAL_CONTEXT_END]"):
            continue
        if line.startswith("Target model:") or line.startswith("Instruction:"):
            continue
        if line.startswith("- "):
            continue
        if line.startswith("<action>") and line.endswith("</action>"):
            continue
        normalized = line.lower().strip()
        if normalized in NOISE_EXACT:
            continue
        if any(token in normalized for token in NOISE_CONTAINS):
            continue
        if len(line) <= 2:
            continue
        if _looks_like_noise(line):
            continue
        if not _looks_like_business_fact(line):
            continue
        lines.append(line[:max_chars])
        if len(lines) >= max_lines:
            break
    return lines


def _looks_like_business_fact(line: str) -> bool:
    low = line.lower()
    if re.search(r"\b20\d{2}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}", low):
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", low):
        return False
    if any(hint in low for hint in BUSINESS_HINTS):
        return True
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", line):
        return True
    if re.search(r"\+?\d(?:[\d\s-]{7,}\d)", line):
        return True
    if _looks_like_question(line):
        return False
    return False


def _looks_like_noise(line: str) -> bool:
    low = line.lower()
    # Very long literary or generic text is usually non-business noise for this app.
    if len(line) > 180 and not _looks_like_business_fact(line):
        return True
    if "春天" in line and "秋天" in line:
        return True
    if "百川" in line and "东" in line:
        return True
    if "少壮不努力" in line:
        return True
    if _looks_like_question(line) and not _looks_like_business_fact(line):
        return True
    return False


def _looks_like_question(line: str) -> bool:
    t = line.strip()
    if not t:
        return False
    if "?" in t or "？" in t:
        return True
    zh_q_prefix = ("如何", "怎么", "哪些", "有没有", "是否", "要不要", "请问")
    return t.startswith(zh_q_prefix)


def slugify_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "customer"
