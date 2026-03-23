from __future__ import annotations

import re

from .contracts import CapsuleRequest, ContextCapsule, KnowledgeBase
from .local_store import LocalKnowledgeStore


class CapsuleBuilder:
    def __init__(self, store: LocalKnowledgeStore, max_facts: int = 12) -> None:
        self.store = store
        self.max_facts = max_facts

    def build(self, req: CapsuleRequest) -> ContextCapsule:
        kb = self.store.load()
        customer = self._resolve_customer(req, kb)
        product = self._resolve_product(req, kb)
        trigger_only = req.user_input.strip() in {"@", ""}

        facts: list[str] = []
        constraints: list[str] = []
        visible_mentions: list[str] = []

        if customer:
            visible_mentions.append(f"@customer:{customer.name}")
            facts.extend(
                [
                    f"Customer id: {customer.customer_id}",
                    f"Customer region: {customer.region or 'unknown'}",
                    f"Preferred currency: {customer.currency}",
                ]
            )
            if customer.price_floor is not None:
                constraints.append(f"Do not quote below {customer.price_floor} {customer.currency} unless user approves.")
            facts.extend([f"Customer note: {note}" for note in customer.notes[:3]])
            facts.extend([f"Recent issue: {issue}" for issue in customer.last_issues[:3]])
        elif trigger_only and kb.customers:
            # When user only types "@", prefer stable structured facts over noisy conversation snippets.
            ranked_customers = sorted(
                kb.customers.values(),
                key=lambda c: (len(c.notes), len(c.last_issues), len(c.tags)),
                reverse=True,
            )
            for c in ranked_customers[:1]:
                facts.extend(
                    [
                        f"Customer id: {c.customer_id}",
                        f"Customer region: {c.region or 'unknown'}",
                        f"Preferred currency: {c.currency}",
                    ]
                )
                facts.extend([f"Customer note: {note}" for note in c.notes[:2]])
                facts.extend([f"Recent issue: {issue}" for issue in c.last_issues[:2]])

        if product:
            visible_mentions.append(f"@product:{product.sku}")
            facts.extend([f"Product sku: {product.sku}", f"Product name: {product.name}"])
            if product.base_price is not None:
                facts.append(f"Reference price: {product.base_price} {product.currency}")
            if product.min_price is not None:
                constraints.append(f"Product min price is {product.min_price} {product.currency}.")

        if kb.preference.must_include:
            constraints.append("Must include: " + "; ".join(kb.preference.must_include[:3]))
        if kb.preference.forbidden_terms:
            constraints.append("Avoid terms: " + "; ".join(kb.preference.forbidden_terms[:5]))
        if kb.preference.pricing_rules:
            constraints.extend([f"Pricing rule: {rule}" for rule in kb.preference.pricing_rules[:3]])

        facts.extend([f"Global fact: {item}" for item in kb.global_facts[:5]])
        doc_top_k = 2 if trigger_only else 8
        structured_for_dedupe = set()
        for item in facts:
            normalized = self._normalize_fact_text(item)
            if normalized:
                structured_for_dedupe.add(normalized)
        facts.extend(
            self._select_relevant_doc_facts(
                req.user_input,
                kb.doc_facts,
                top_k=doc_top_k,
                exclude_normalized=structured_for_dedupe,
            )
        )

        trimmed_facts = [fact for fact in facts if fact][: self.max_facts]
        summary = (
            "Local capsule generated for trade assistant. "
            f"Resolved customer={customer.name if customer else 'none'}, "
            f"product={product.sku if product else 'none'}."
        )

        prompt = self._render_prompt(
            user_input=req.user_input,
            model_name=req.model_name,
            facts=trimmed_facts,
            constraints=constraints[: self.max_facts],
            template_lang=req.template_lang,
            template_mode=req.template_mode,
            custom_instruction=req.custom_instruction,
        )
        return ContextCapsule(
            summary=summary,
            facts=trimmed_facts,
            constraints=constraints[: self.max_facts],
            visible_mentions=visible_mentions,
            injected_prompt=prompt,
        )

    def _resolve_customer(self, req: CapsuleRequest, kb: KnowledgeBase):
        hint = req.customer_hint.strip()
        if hint:
            return self.store.find_customer(hint, kb=kb)
        q = req.user_input.lower()
        for customer in kb.customers.values():
            if customer.name.lower() in q:
                return customer
        return None

    def _resolve_product(self, req: CapsuleRequest, kb: KnowledgeBase):
        hint = req.product_hint.strip()
        if hint:
            return self.store.find_product(hint, kb=kb)
        q = req.user_input.lower()
        for product in kb.products.values():
            if product.sku.lower() in q or product.name.lower() in q:
                return product
        return None

    def _select_relevant_doc_facts(
        self,
        query: str,
        doc_facts: list[str],
        top_k: int = 8,
        exclude_normalized: set[str] | None = None,
    ) -> list[str]:
        if not doc_facts:
            return []
        excludes = exclude_normalized or set()
        tokens = self._tokenize(query)
        scored: list[tuple[float, int, str]] = []
        total = len(doc_facts)
        clean_query = query.strip()
        for idx, raw in enumerate(doc_facts):
            text = str(raw).strip()
            if not text:
                continue
            if self._is_noise_fact(text):
                continue
            normalized = self._normalize_fact_text(text)
            if normalized and normalized in excludes:
                continue
            text_l = text.lower()
            overlap = sum(1 for t in tokens if t and t in text_l)
            exact_bonus = 2 if clean_query and clean_query.lower() in text_l else 0
            business_bonus = 2 if self._is_business_fact(text) else 0
            recency = (idx + 1) / max(1, total)
            score = float(overlap * 3 + exact_bonus + business_bonus) + recency
            if score <= 0:
                continue
            scored.append((score, idx, text))

        if not scored:
            fallback = [x for x in reversed(doc_facts) if self._is_business_fact(str(x)) and not self._is_noise_fact(str(x))]
            fallback = list(reversed(fallback[:top_k]))
            return [f"Doc fact: {x}" for x in fallback]

        if not tokens:
            # For trigger-only queries like "@", avoid generic/noisy facts and keep business-heavy items.
            scored = [item for item in scored if self._is_business_fact(item[2])]
            if not scored:
                fallback = [x for x in reversed(doc_facts) if self._is_business_fact(str(x)) and not self._is_noise_fact(str(x))]
                fallback = list(reversed(fallback[:top_k]))
                return [f"Doc fact: {x}" for x in fallback]

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [f"Doc fact: {item[2]}" for item in scored[:top_k]]

    def _tokenize(self, query: str) -> list[str]:
        q = query.lower().strip()
        if not q:
            return []
        parts = re.findall(r"[a-z0-9_@.-]+|[\u4e00-\u9fff]{1,6}", q)
        return [p for p in parts if len(p) >= 2]

    def _is_noise_fact(self, text: str) -> bool:
        low = text.lower().strip()
        if low in {"[doubao-web] user request: @", "user request: @", "追问", "复制", "快速"}:
            return True
        noisy_tokens = [
            "user request:",
            "用户请求:",
            "key facts",
            "最终注入 prompt",
            "追问",
            "复制",
        ]
        if any(token in low for token in noisy_tokens):
            return True
        if self._looks_like_question(text):
            return True
        if re.search(r"\b20\d{2}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}", low):
            return True
        if re.fullmatch(r"\[.*?回复\]\s*20\d{2}-\d{2}-\d{2}.*", text.strip()):
            return True
        if len(text) > 200 and not self._is_business_fact(text):
            return True
        if "少壮不努力" in text or ("春天" in text and "秋天" in text):
            return True
        return False

    def _is_business_fact(self, text: str) -> bool:
        low = text.lower()
        if re.search(r"\b20\d{2}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}", low):
            return False
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", low):
            return False
        if self._looks_like_question(text):
            return False
        hints = [
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
        if any(h in low for h in hints):
            return True
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
            return True
        if re.search(r"\+?\d(?:[\d\s-]{7,}\d)", text):
            return True
        return False

    def _looks_like_question(self, text: str) -> bool:
        t = text.strip()
        if not t:
            return False
        if "?" in t or "？" in t:
            return True
        zh_q_prefix = ("如何", "怎么", "哪些", "有没有", "是否", "要不要", "请问")
        return t.startswith(zh_q_prefix)

    def _normalize_fact_text(self, text: str) -> str:
        t = text.strip()
        if not t:
            return ""
        t = re.sub(r"^\[[^\]]+\]\s*", "", t)
        t = re.sub(
            r"^(Doc fact:|Global fact:|Customer note:|Recent issue:|Customer id:|Customer region:|Preferred currency:)\s*",
            "",
            t,
            flags=re.IGNORECASE,
        )
        return t.strip().lower()

    def _render_prompt(
        self,
        user_input: str,
        model_name: str,
        facts: list[str],
        constraints: list[str],
        template_lang: str = "zh",
        template_mode: str = "standard",
        custom_instruction: str = "",
    ) -> str:
        use_zh = template_lang.lower().startswith("zh")
        mode = (template_mode or "standard").lower()
        lines = ["[LOCAL_CONTEXT_BEGIN]"]
        if model_name:
            lines.append(f"Target model: {model_name}")

        if facts:
            lines.append("已知信息:" if use_zh else "Known facts:")
            lines.extend([f"- {self._localize_fact(item, use_zh)}" for item in facts])
        if constraints:
            lines.append("约束条件:" if use_zh else "Constraints:")
            lines.extend([f"- {self._localize_constraint(item, use_zh)}" for item in constraints])

        if mode == "custom" and custom_instruction.strip():
            if use_zh:
                lines.extend(
                    [
                        "自定义指令:",
                        custom_instruction.strip(),
                        "- 如需执行动作，只追加一个动作标签:",
                        '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                        "[LOCAL_CONTEXT_END]",
                        "",
                        f"用户请求: {user_input}",
                    ]
                )
            else:
                lines.extend(
                    [
                        "Custom instruction:",
                        custom_instruction.strip(),
                        "- If an action is needed, append a single action tag:",
                        '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                        "[LOCAL_CONTEXT_END]",
                        "",
                        f"User request: {user_input}",
                    ]
                )
            return "\n".join(lines)

        if mode == "compact":
            if use_zh:
                lines.extend(
                    [
                        "指令：直接给出最短可执行答复，避免解释。",
                        "- 如需执行动作，只追加一个动作标签:",
                        '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                        "[LOCAL_CONTEXT_END]",
                        "",
                        f"用户请求: {user_input}",
                    ]
                )
            else:
                lines.extend(
                    [
                        "Instruction: Give the shortest executable answer with minimal explanation.",
                        "- If an action is needed, append a single action tag:",
                        '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                        "[LOCAL_CONTEXT_END]",
                        "",
                        f"User request: {user_input}",
                    ]
                )
            return "\n".join(lines)

        if use_zh:
            lines.extend(
                [
                    "指令:",
                    "- 请基于以上上下文输出最终答复。",
                    "- 如需执行动作，只追加一个动作标签:",
                    '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                    "[LOCAL_CONTEXT_END]",
                    "",
                    f"用户请求: {user_input}",
                ]
            )
        else:
            lines.extend(
                [
                    "Instruction:",
                    "- Draft the response using the context above.",
                    "- If an action is needed, append a single action tag:",
                    '<action>generate_quote_draft:{"client":"...","product":"...","price":0,"currency":"USD"}</action>',
                    "[LOCAL_CONTEXT_END]",
                    "",
                    f"User request: {user_input}",
                ]
            )
        return "\n".join(lines)

    def _localize_fact(self, text: str, use_zh: bool) -> str:
        if not use_zh:
            return text
        replacements = {
            "Customer id:": "客户ID:",
            "Customer region:": "客户地区:",
            "Preferred currency:": "常用币种:",
            "Customer note:": "客户备注:",
            "Recent issue:": "近期问题:",
            "Product sku:": "产品SKU:",
            "Product name:": "产品名称:",
            "Reference price:": "参考价格:",
            "Global fact:": "全局记忆:",
            "Doc fact:": "文档记忆:",
            "[gemini-web]": "[Gemini回复]",
            "[doubao-web]": "[豆包回复]",
            "[deepseek-web]": "[DeepSeek回复]",
            "[qwen-web]": "[千问回复]",
            "[web-llm]": "[模型回复]",
        }
        out = text
        for src, dst in replacements.items():
            out = out.replace(src, dst)
        return out

    def _localize_constraint(self, text: str, use_zh: bool) -> str:
        if not use_zh:
            return text
        replacements = {
            "Do not quote below": "报价不得低于",
            "unless user approves.": "，除非用户明确同意。",
            "Product min price is": "产品最低价为",
            "Must include:": "必须包含:",
            "Avoid terms:": "避免用词:",
            "Pricing rule:": "定价规则:",
        }
        out = text
        for src, dst in replacements.items():
            out = out.replace(src, dst)
        return out
