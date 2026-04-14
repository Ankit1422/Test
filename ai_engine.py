# ai_engine.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Gemini client via OpenAI-compatible endpoint
# ---------------------------------------------------------------------------

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL = "gemini-2.0-flash"


# ===========================================================================
# Function 1: Transaction Categorizer
# ===========================================================================

def categorize_transaction(description: str) -> str:
    """Send a transaction description to Gemini and return a single
    category word.

    Args:
        description: Raw transaction description, e.g. 'Whole Foods Market'

    Returns:
        A single category string, e.g. 'Groceries'
        Falls back to 'Uncategorised' if the API call fails.

    Example:
        >>> categorize_transaction("Netflix monthly subscription")
        'Entertainment'
    """
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,        # zero temperature = deterministic, consistent output
        max_tokens=10,        # category is one word — no need for more tokens
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial transaction categorizer. "
                    "Your only job is to classify a transaction description "
                    "into exactly ONE category word from this list: "
                    "Groceries, Utilities, Entertainment, Transportation, "
                    "Dining, Healthcare, Shopping, Education, Travel, "
                    "Subscriptions, Rent, Salary, Investment, Other. "
                    "Rules: "
                    "1. Reply with ONLY the single category word — no punctuation, "
                    "no explanation, no extra words. "
                    "2. If you are unsure, reply with 'Other'."
                ),
            },
            {
                "role": "user",
                "content": description,
            },
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Guard: if the model returns more than one word despite instructions, take the first
    category = raw.split()[0] if raw else "Uncategorised"
    return category


# ===========================================================================
# Function 2: Investment Suggestion Generator
# ===========================================================================

def generate_investment_suggestion(surplus_amount: float) -> str:
    """Ask Gemini for a concise 2-sentence investment suggestion based on
    the user's monthly surplus.

    Args:
        surplus_amount: The user's monthly surplus in dollars, e.g. 450.00

    Returns:
        A 2-sentence plain-text suggestion string.

    Example:
        >>> generate_investment_suggestion(450.00)
        'Consider putting $225 into a high-yield savings account for liquidity...'
    """
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,      # slight creativity for varied, natural suggestions
        max_tokens=80,        # 2 sentences fits comfortably within 80 tokens
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cautious, practical personal finance advisor "
                    "specialising in short-term wealth building for everyday people. "
                    "You give clear, safe, beginner-friendly advice. "
                    "Never recommend high-risk assets like crypto or penny stocks. "
                    "Always respond in exactly 2 sentences."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"I have a monthly surplus of ${surplus_amount:.2f}. "
                    "Give me a concise 2-sentence suggestion on how to safely "
                    "allocate or invest this amount for short-term growth."
                ),
            },
        ],
    )

    return response.choices[0].message.content.strip()
print(categorize_transaction("UBER *TRIP SF"))
