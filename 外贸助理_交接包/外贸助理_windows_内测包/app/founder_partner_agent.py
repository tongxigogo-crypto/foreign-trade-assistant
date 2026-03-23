from __future__ import annotations

"""Legacy module kept for compatibility with previous scaffolding."""


class FounderPartnerAgent:  # pragma: no cover
    def __init__(self, *_args, **_kwargs) -> None:
        raise RuntimeError(
            "FounderPartnerAgent is deprecated in this project. "
            "Use the trade assistant pipeline in app.main instead."
        )
