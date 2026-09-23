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
# that category. Keywords are matched as whole words, and the longest match
# across all categories wins, so a keyword only needs to be specific enough
# to be unambiguous -- it does not need to be listed before another one.
CATEGORY_RULES: dict[str, list[str]] = {
    "Groceries": [
        "supermarket", "grocery", "market", "carrefour", "coto", "dia",
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
        "movistar", "claro", "personal flow", "personal pago", "tim",
        "vodafone", "phone bill",
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


def _pattern_for(keyword: str) -> str:
    """Build a whole-word pattern for one keyword.

    Word boundaries matter more than they look. Without them "dia" (the
    supermarket chain) matches "guardia", "personal" (the phone carrier)
    matches "personal trainer", and "bar" matches "barberia". A trailing `%`
    means "this word may continue", for brands written with a suffix.
    """
    escaped = re.escape(_normalize(keyword))
    if escaped.endswith(r"\%"):
        return r"\b" + escaped[:-2] + r"\w*"
    return r"\b" + escaped + r"\b"


def categorize(description: str) -> str:
    """
    Guess a spending category from a free-text description.

    Every rule is tested, and the longest matching keyword wins: "uber eats"
    beats "uber", so a food delivery is Dining and not Transport regardless of
    the order the categories happen to be written in. Ties fall back to the
    order of CATEGORY_RULES. Returns DEFAULT_CATEGORY when nothing matches.
    """
    if not description:
        return DEFAULT_CATEGORY

    normalized = _normalize(description)

    best_category = DEFAULT_CATEGORY
    best_length = 0
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if re.search(_pattern_for(keyword), normalized):
                if len(keyword) > best_length:
                    best_category, best_length = category, len(keyword)

    return best_category


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
