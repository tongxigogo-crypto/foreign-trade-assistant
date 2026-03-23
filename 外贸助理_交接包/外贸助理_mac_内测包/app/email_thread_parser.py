from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedEmailThread:
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    company_name: str = ""
    country_or_region: str = ""
    products: list[str] = field(default_factory=list)
    trade_terms: list[str] = field(default_factory=list)
    ports: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    summary_facts: list[str] = field(default_factory=list)


def parse_email_thread_text(text: str) -> ParsedEmailThread:
    lower = text.lower()
    result = ParsedEmailThread()

    customer_match = re.search(r"([A-Za-z][A-Za-z\s]+)\s*<([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})>", text)
    if customer_match:
        result.customer_name = customer_match.group(1).strip()
        result.customer_email = customer_match.group(2).strip()

    # Prefer first non-company external email sender in thread.
    all_pairs = re.findall(r"([A-Za-z][A-Za-z\s]+)\s*<([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})>", text)
    for name, email in all_pairs:
        if "qifawpc.cn" not in email.lower():
            result.customer_name = name.strip()
            result.customer_email = email.strip()
            break

    phone_match = re.search(r"(\+\d{6,15})", text)
    if phone_match:
        result.customer_phone = phone_match.group(1)

    company_match = re.search(r"samples from ([A-Za-z0-9\s&.,-]+)\(", text, re.IGNORECASE)
    if company_match:
        result.company_name = company_match.group(1).strip()

    product_codes = sorted(set(re.findall(r"\b(?:FCG|ECG)-\d{2}[A-Z]?\b", text)))
    result.products = product_codes

    terms: list[str] = []
    if "fob" in lower:
        terms.append("FOB")
    if "cif" in lower:
        terms.append("CIF")
    result.trade_terms = terms

    port_matches = re.findall(r"porto de [A-Za-zÀ-ÿ]+|Leix[õo]es|Matosinhos|Porto", text, re.IGNORECASE)
    result.ports = sorted(set(item.strip() for item in port_matches if item.strip()))

    issues: list[str] = []
    if "first time" in lower and "payment" in lower:
        issues.append("First international payment difficulty.")
    if "opening the new company" in lower or "bureaucracy" in lower:
        issues.append("Customer onboarding delayed due to company setup bureaucracy.")
    if "delayed response" in lower:
        issues.append("Response delay acknowledged in thread.")
    result.issues = issues

    facts: list[str] = []
    if result.customer_name:
        facts.append(f"Customer: {result.customer_name}")
    if result.customer_email:
        facts.append(f"Email: {result.customer_email}")
    if result.customer_phone:
        facts.append(f"Phone: {result.customer_phone}")
    if result.company_name:
        facts.append(f"Company mention: {result.company_name}")
    if result.products:
        facts.append("Interested SKUs: " + ", ".join(result.products))
    if result.trade_terms:
        facts.append("Trade terms discussed: " + ", ".join(result.trade_terms))
    if result.ports:
        facts.append("Destination ports discussed: " + ", ".join(result.ports))
    facts.extend([f"Issue: {issue}" for issue in result.issues])
    result.summary_facts = facts

    if "portugal" in lower:
        result.country_or_region = "Portugal"

    return result


def parse_email_thread_file(path: Path) -> ParsedEmailThread:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return parse_email_thread_text(text)
