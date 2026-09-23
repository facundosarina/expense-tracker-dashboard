"""
Tests for the categorization rules. Run with:  python -m pytest -q

The interesting cases are the ones where a naive substring match gets it
wrong -- those are the reason the matcher uses word boundaries and prefers
the longest keyword.
"""

from categorizer import DEFAULT_CATEGORY, categorize


def test_obvious_merchants():
    assert categorize("COTO SUPERMERCADO CABA") == "Groceries"
    assert categorize("UBER *TRIP") == "Transport"
    assert categorize("NETFLIX.COM") == "Entertainment"
    assert categorize("Transferencia alquiler septiembre") == "Housing"


def test_accents_and_case_do_not_matter():
    assert categorize("farmacia italiana roma") == "Health"
    assert categorize("FARMACÍA ITALIANA ROMA") == "Health"


def test_the_longest_keyword_wins():
    # "uber eats" beats "uber": a food delivery is Dining, not Transport.
    assert categorize("UBER EATS pedido") == "Dining"
    assert categorize("UBER *TRIP") == "Transport"


def test_whole_words_only():
    # Each of these contains a keyword as a substring but means something else.
    assert categorize("Guardia médica nocturna") != "Groceries"   # "dia" in "guardia"
    assert categorize("PERSONAL TRAINER mensual") != "Utilities"  # "personal" the carrier
    assert categorize("BARBERIA Don Luis") != "Dining"            # "bar" in "barberia"
    assert categorize("Curso de marketing digital") == "Education"  # "market" in "marketing"


def test_unknown_descriptions_fall_back():
    assert categorize("Random unknown merchant XYZ") == DEFAULT_CATEGORY
    assert categorize("") == DEFAULT_CATEGORY
    assert categorize("   ") == DEFAULT_CATEGORY
