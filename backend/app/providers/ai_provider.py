from __future__ import annotations

from typing import Any

from app.providers.base_provider import BaseProvider
from app.providers.gemini_client import GeminiError, generate


def _prefs_summary(context: dict) -> str:
    assets = context.get("interested_assets") or []
    investor_type = context.get("investor_type") or "unknown"
    content = context.get("content_preferences") or []
    return (
        f"assets={','.join(assets) or 'none'}; "
        f"investor_type={investor_type}; "
        f"content={','.join(content) or 'none'}"
    )


def _prices_summary(context: dict) -> str:
    prices = (context.get("prices") or {}).get("prices") or context.get("prices") or {}
    if not isinstance(prices, dict) or not prices:
        return "no live prices"
    parts = []
    for asset, row in list(prices.items())[:6]:
        if not isinstance(row, dict):
            continue
        usd = row.get("usd")
        change = row.get("change_24h")
        parts.append(f"{asset}: ${usd} ({change}% 24h)")
    return "; ".join(parts) if parts else "no live prices"


def build_template_insight(context: dict) -> dict:
    assets = context.get("interested_assets") or ["bitcoin"]
    investor_type = context.get("investor_type") or "hodler"
    focus = ", ".join(assets[:3])
    text = (
        f"Today's focus for a {investor_type}: watch {focus}. "
        "Stay disciplined with your plan and treat short-term moves as noise "
        "unless they change your thesis."
    )
    return {"insight_text": text, "generated_by": "template"}


class TemplateInsightProvider(BaseProvider):
    section = "insight"
    name = "template"

    def __init__(self, config: Any | None = None):
        self.config = config

    def fetch(self, context: dict) -> dict:
        return build_template_insight(context)

    def static_fallback(self, context: dict) -> dict:
        return build_template_insight(context)


class GeminiInsightProvider(BaseProvider):
    section = "insight"
    name = "gemini"

    def __init__(self, config: Any | None = None):
        self.config = config

    def fetch(self, context: dict) -> dict:
        prompt = (
            "You are a concise crypto market assistant. "
            "Write 2-3 short sentences of educational insight (not financial advice) "
            "personalized to this user.\n"
            f"Preferences: {_prefs_summary(context)}\n"
            f"Prices: {_prices_summary(context)}\n"
            "Return plain text only."
        )
        try:
            text = generate(prompt, self.config)
            return {"insight_text": text, "generated_by": "gemini"}
        except GeminiError:
            # Soft fallback so the insight section still succeeds.
            result = build_template_insight(context)
            result["generated_by"] = "template_fallback"
            return result

    def static_fallback(self, context: dict) -> dict:
        return build_template_insight(context)
