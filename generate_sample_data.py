"""
generate_sample_data.py

Creates a fictional expenses.csv so the dashboard has something to show
out of the box. No real financial data is used anywhere in this project.

Run with: python generate_sample_data.py
"""

import csv
import random
from datetime import date, timedelta

from categorizer import categorize

random.seed(7)

MERCHANTS = [
    ("COTO SUPERMERCADO", 8, (2000, 15000)),
    ("CARREFOUR EXPRESS", 6, (1500, 9000)),
    ("PEDIDOSYA - Sushi Club", 4, (3500, 8000)),
    ("UBER *TRIP", 10, (900, 4500)),
    ("CABIFY", 5, (900, 4000)),
    ("NETFLIX.COM", 1, (2500, 2500)),
    ("SPOTIFY PREMIUM", 1, (1800, 1800)),
    ("FARMACIA ITALIANA", 3, (1200, 6000)),
    ("MOVISTAR FACTURA", 1, (9000, 9000)),
    ("EDESUR FACTURA", 1, (7000, 12000)),
    ("Transferencia alquiler", 1, (180000, 180000)),
    ("MERCADOLIBRE", 3, (4000, 22000)),
    ("ZARA", 1, (15000, 40000)),
    ("Curso Udemy", 1, (3000, 6000)),
    ("Café con amigos", 6, (1200, 3500)),
    ("Nafta YPF", 4, (8000, 15000)),
    ("Cine Hoyts", 1, (5000, 9000)),
]

START = date(2026, 4, 1)
DAYS = 180  # ~6 months of history

rows = []
for merchant, occurrences_per_month, (lo, hi) in MERCHANTS:
    total_occurrences = round(occurrences_per_month * (DAYS / 30))
    for _ in range(total_occurrences):
        offset = random.randint(0, DAYS - 1)
        txn_date = START + timedelta(days=offset)
        amount = round(random.uniform(lo, hi), 2)
        rows.append(
            {
                "date": txn_date.isoformat(),
                "description": merchant,
                "amount": amount,
                "category": categorize(merchant),
            }
        )

rows.sort(key=lambda r: r["date"])

with open("data/expenses.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "category"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} fictional transactions to data/expenses.csv")
