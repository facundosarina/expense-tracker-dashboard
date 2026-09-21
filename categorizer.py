"""
categorizer.py

Small rule-based auto-categorization engine for expense descriptions.

This is the "automation" piece of the project: instead of the user manually
picking a category for every single transaction, this module looks at the
free-text description (e.g. what you'd get from a bank statement or a
manually-typed note) and guesses the right category from a keyword table.

It's intentionally simple (no ML, no external API) so it's easy to read,
easy to extend, and has zero dependencies beyond the standard library.
Keywords cover both English and Spanish merchant/description wording,
since real bank statements are rarely in just one language.
"""

from __future__ import annotations

import re

# Category -> list of keywords that, if found in the description, suggest
# that category. Order matters: the first category with a match wins, so
# more specific categories are listed before more generic ones.
CATEGORY_RULES: dict[str, list[str]] = {
    "Groceries": [
        "supermarket", "grocery", "market", "carrefour", "coto", "dia%",
        "jumbo", "walmart", "whole foods", "aldi", "lidl", "esselunga",
        "conad", "verduleria", "carniceria", "almacen",
    ],
    "Dining": [
        "restaurant", "cafe", "coffee", "bar", "pizza", "sushi",
        "mcdonald", "burger", "starbucks", "rappi", "pedidosya",
        "glovo", "deliveroo", "uber eats", "resto", "bodegon",
        "heladeria", "panaderia",
    ],
    "Transport": [
        "uber", "taxi", "cabify", "didi", "metro", "subte", "bus",
        "train", "treno", "trenitalia", "gasoline", "gasolina",
        "nafta", "fuel", "parking", "estacionamiento", "peaje", "toll",
    ],
    "Utilities": [
        "electric", "electricidad", "edenor", "edesur", "gas natural",
        "water bill", "agua", "internet", "wifi", "fibra", "telecom",
        "movistar", "claro", "personal", "tim", "vodafone", "phone bill",
    ],
    "Health": [
        "pharmacy", "farmacia", "farmacia italiana", "doctor", "medico",
        "hospital", "clinica", "dentist", "dentista", "insurance medica",
    ],
    "Entertainment": [
        "netflix", "spotify", "disney", "hbo", "prime video", "cinema",
        "cine", "teatro", "concert", "concierto", "steam", "playstation",
        "xbox",
    ],
    "Shopping": [
        "amazon", "mercadolibre", "mercado libre", "zara", "h&m",
        "shein", "aliexpress", "shopping", "mall", "tienda",
    ],
    "Housing": [
        "rent", "alquiler", "expensas", "mortgage", "hipoteca",
    ],
    "Education": [
        "curso", "course", "udemy", "coursera", "universidad",
        "university", "libreria", "bookstore",
    ],
}

# Fallback category when nothing matches.
DEFAULT_CATEGORY = "Other"


def _normalize(text: str) -> str:
    """Lowercase and strip accents/extra punctuation for looser matching."""
    text = text.lower().strip()
    # Very small accent-folding table, just enough for common Spanish/Italian
    # merchant names (avoids pulling in a dependency like `unidecode`).
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
    }
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    return text


def categorize(description: str) -> str:
    """
    Guess a spending category from a free-text description.

    Returns the first category whose keyword list matches, or
    DEFAULT_CATEGORY ("Other") if nothing matches.
    """
    if not description:
        return DEFAULT_CATEGORY

    normalized = _normalize(description)

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            pattern = re.escape(_normalize(keyword)).replace(r"\%", ".*")
            if re.search(pattern, normalized):
                return category

    return DEFAULT_CATEGORY


def categorize_many(descriptions: list[str]) -> list[str]:
    """Vectorized convenience wrapper over `categorize`."""
    return [categorize(d) for d in descriptions]


if __name__ == "__main__":
    # Quick manual smoke test: `python categorizer.py`
    samples = [
        "COTO SUPERMERCADO CABA",
        "UBER *TRIP",
        "NETFLIX.COM",
        "Farmacia Italiana Roma",
        "PEDIDOSYA - Sushi Club",
        "Transferencia alquiler septiembre",
        "Random unknown merchant XYZ",
    ]
    for s in samples:
        print(f"{s!r:45} -> {categorize(s)}")
