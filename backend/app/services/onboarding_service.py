import sqlite3

from app.repositories.preferences_repository import save_preferences

QUESTIONS = [
    {
        "id": "interested_assets",
        "prompt": "What crypto assets are you interested in?",
        "type": "multi",
        "options": [
            {"id": "bitcoin", "label": "Bitcoin"},
            {"id": "ethereum", "label": "Ethereum"},
            {"id": "solana", "label": "Solana"},
            {"id": "xrp", "label": "XRP"},
            {"id": "cardano", "label": "Cardano"},
            {"id": "dogecoin", "label": "Dogecoin"},
        ],
    },
    {
        "id": "investor_type",
        "prompt": "What type of investor are you?",
        "type": "single",
        "options": [
            {"id": "hodler", "label": "HODLer"},
            {"id": "day_trader", "label": "Day Trader"},
            {"id": "nft_collector", "label": "NFT Collector"},
        ],
    },
    {
        "id": "content_preferences",
        "prompt": "What kind of content would you like to see?",
        "type": "multi",
        "options": [
            {"id": "market_news", "label": "Market News"},
            {"id": "charts", "label": "Charts"},
            {"id": "social", "label": "Social"},
            {"id": "fun", "label": "Fun"},
        ],
    },
]


def get_questions() -> list[dict]:
    """Return the onboarding quiz questions."""
    return QUESTIONS


def save_answers(conn: sqlite3.Connection, user_id: int, answers: dict) -> dict:
    """Save quiz answers and mark onboarding complete."""
    return save_preferences(
        conn,
        user_id=user_id,
        answers=answers,
        onboarding_completed=True,
    )
