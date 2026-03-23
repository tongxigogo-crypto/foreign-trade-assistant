from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    region: str = ""
    currency: str = "USD"
    price_floor: float | None = None
    last_issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductRecord:
    sku: str
    name: str
    base_price: float | None = None
    min_price: float | None = None
    currency: str = "USD"
    specs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserPreference:
    tone: str = "professional"
    forbidden_terms: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    pricing_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeBase:
    customers: dict[str, CustomerProfile] = field(default_factory=dict)
    products: dict[str, ProductRecord] = field(default_factory=dict)
    preference: UserPreference = field(default_factory=UserPreference)
    global_facts: list[str] = field(default_factory=list)
    doc_facts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customers": {key: value.to_dict() for key, value in self.customers.items()},
            "products": {key: value.to_dict() for key, value in self.products.items()},
            "preference": self.preference.to_dict(),
            "global_facts": list(self.global_facts),
            "doc_facts": list(self.doc_facts),
        }


@dataclass
class CapsuleRequest:
    user_input: str
    customer_hint: str = ""
    product_hint: str = ""
    model_name: str = ""
    template_lang: str = "zh"
    template_mode: str = "standard"
    custom_instruction: str = ""


@dataclass
class ContextCapsule:
    summary: str
    facts: list[str]
    constraints: list[str]
    visible_mentions: list[str]
    injected_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionCommand:
    name: str
    payload: dict[str, Any]
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionExecutionResult:
    status: str
    message: str
    artifacts: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
