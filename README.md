# Expense Tracker Dashboard

A personal expense tracker with automatic category detection, built in
[Python](https://www.python.org) with [Streamlit](https://streamlit.io)
and [Plotly](https://plotly.com/python/). It's a small, self-contained
companion piece to [n8n-request-tracker](https://github.com/facundosarina/n8n-request-tracker),
showing the same "turn manual, repetitive work into something automatic"
approach applied with plain Python instead of a no-code workflow tool.

**Live demo:** https://facundosarina-expense-tracker.streamlit.app/

Sample data is fictional — no real financial information is included. The demo
is safe to poke at: the sample file is read once and then lives in your own
browser session, so anything you add or import is yours alone and is never
written back to the server.

## Problem it solves

Tracking personal (or small business) spending by hand means manually
tagging every transaction with a category before you can see where the
money actually goes. That step is tedious and easy to skip, which is
usually why the spreadsheet stops getting updated after a few weeks.

This app removes that step: every transaction — typed in one at a time or
imported in bulk from a CSV — gets a category guessed automatically from
its description, and the dashboard updates immediately.

## How it works

1. **Automatic categorization (`categorizer.py`)** — a small rule-based
   engine matches each transaction's description against a keyword table
   (e.g. "UBER", "COTO SUPERMERCADO", "NETFLIX") and returns the most likely
   category. No ML model or external API — just a readable, easy-to-extend
   set of rules. Keywords cover both English and Spanish merchant names,
   since real bank statements are rarely in a single language.
2. **Manual entry** — add one transaction at a time; the suggested category
   appears as soon as you type the description, and can always be overridden
   before saving.
3. **Bulk import** — upload a CSV with `date, description, amount` and every
   row gets auto-categorized before it's added, with a preview so you can
   check the results first.
4. **Dashboard (`app.py`)** — filter by date range and category, and see:
   total spent, transaction count, average transaction, top category, a
   by-category breakdown and a month-by-month trend. Category totals are drawn
   as horizontal bars rather than a pie, because nine slices of a donut cannot
   be compared by eye.

![Dashboard screenshot](dashboard_screenshot.png)

## Try it / reuse it

```bash
pip install -r requirements.txt
python generate_sample_data.py   # optional: creates fictional sample data
streamlit run app.py
python -m pytest -q              # the categorization rules, 5 tests
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

To adapt it to your own spending, either edit `data/expenses.csv` directly,
or clear it and use the "Add a transaction" / "Import transactions from CSV"
sections in the app. To add or tweak categories, edit `CATEGORY_RULES` in
`categorizer.py` — it's a plain dictionary of `category -> keywords`.

## Known limits

- **Categorization is keyword-based, not ML-based.** It's transparent and
  easy to extend, but a merchant name it has never seen (and that doesn't
  contain any known keyword) falls back to "Other" until a matching keyword
  is added. Keywords match whole words and the longest match wins, so
  "UBER EATS" is Dining rather than Transport, and "BARBERIA" is not read as
  a bar — the cases that a plain substring search gets wrong are covered in
  `test_categorizer.py`.
- **Nothing is persisted.** The bundled CSV seeds each visitor's session and
  is never written to. That is deliberate for a public demo — one visitor's
  test data must not become the next visitor's starting point — but it does
  mean your own entries disappear when you close the tab. Use "Download this
  data" to keep them. A real personal-use version would need a database and a
  login before storing anyone's actual finances.
- **Single currency.** Amounts are treated as ARS throughout; there is no
  conversion.

## Stack

Python · Streamlit · Pandas · Plotly.

## About me

I build automations that take manual, repetitive work — form intake,
document requests, case tracking, spending/data organization — and turn it
into a process that runs itself. Before automation I spent 8+ years running
exactly this kind of process by hand in an administrative/legal setting,
so I know firsthand which parts actually need to be reliable.

Available for freelance automation work — [Workana](https://www.workana.com/freelancer/e77e2133ac2a73aacd51029bb5e7f473) · [LinkedIn](https://www.linkedin.com/in/facundo-sarina/)
