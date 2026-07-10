from unittest.mock import patch

from app.config import TestConfig
from app.providers.ai_provider import GeminiInsightProvider, TemplateInsightProvider
from app.providers.gemini_client import GeminiError


def test_template_insight_success():
    provider = TemplateInsightProvider(TestConfig)
    data = provider.fetch(
        {
            "interested_assets": ["bitcoin", "ethereum"],
            "investor_type": "hodler",
        }
    )
    assert data["generated_by"] == "template"
    assert "bitcoin" in data["insight_text"]
    assert "hodler" in data["insight_text"]


def test_gemini_insight_success():
    provider = GeminiInsightProvider(TestConfig)
    with patch(
        "app.providers.ai_provider.generate",
        return_value="BTC looks steady for long-term holders.",
    ):
        data = provider.fetch({"interested_assets": ["bitcoin"], "investor_type": "hodler"})

    assert data["generated_by"] == "gemini"
    assert "BTC" in data["insight_text"]


def test_gemini_insight_falls_back_to_template():
    provider = GeminiInsightProvider(TestConfig)
    with patch(
        "app.providers.ai_provider.generate",
        side_effect=GeminiError("down"),
    ):
        data = provider.fetch(
            {
                "interested_assets": ["solana"],
                "investor_type": "day_trader",
            }
        )

    assert data["generated_by"] == "template_fallback"
    assert "solana" in data["insight_text"]
    assert "day_trader" in data["insight_text"]


def test_template_static_fallback():
    data = TemplateInsightProvider(TestConfig).static_fallback({})
    assert data["generated_by"] == "template"
    assert data["insight_text"]
