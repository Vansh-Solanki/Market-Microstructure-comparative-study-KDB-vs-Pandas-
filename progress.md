# Progress Log

Status tracker for the kdb+/q vs Python market microstructure project. Update this file as phases complete, don't delete history, append below each entry.

---

## Current status: Phase 2 complete (q port validated row-for-row against Python)

## Environment

- **q/kdb+**: installed and working, confirmed in Phase 0. Lives inside the WSL Ubuntu distro at `/home/vansh/.kx/bin/q`, with `QHOME=/home/vansh/.kx` set in `~/.bashrc`. Verified with `q -q <<< '1+1'` → `2`. Repo lives under `/mnt/c/...` from WSL's perspective, so q scripts in `q/` can be run directly from a WSL shell in this directory (`q q/schema.q` etc. once written). No venv needed for q since it runs natively in WSL, not through Python.
- **Q for Mortals**: chapters 1-9 completed, hands-on practice done.
- **Python**: pandas available (used already for LOBSTER parsing below).

## Data status: Done

Real trade/quote data pulled from LOBSTER's free sample files (AAPL, AMZN, GOOG, INTC, MSFT, all from 2012-06-21, level 1). Parsed with `parse_lobster.py` into a unified schema:

| File | Rows |
|---|---|
| `all_trades.csv` | 123,984 |
| `all_quotes.csv` | 1,041,889 |

Per-symbol breakdown:

| Symbol | Trades | Quotes |
|---|---|---|
| AAPL | 34,990 | 118,497 |
| AMZN | 11,419 | 57,515 |
| GOOG | 11,678 | 49,482 |
| INTC | 32,483 | 404,986 |
| MSFT | 33,414 | 411,409 |

Schema:
- **trade**: `time, sym, price, size, side` (side derived from LOBSTER's direction field: a resting sell limit order executed = buyer-initiated = `buy`; a resting buy limit order executed = `sell`)
- **quote**: `time, sym, bid, ask, bidSize, askSize`

Validated: `pd.merge_asof` (asof join) run across the combined multi-symbol set, **zero unmatched trades**. Correctness confirmed against real market data.

No synthetic data used or planned. This is a deliberate choice.

## Decisions log (chronological, most recent last)

- Build order: **Python first** (reference implementation), then port to q. Rationale: avoids conflating "unfamiliar language" slowness with genuine engine differences in the benchmark.
- Data source: LOBSTER free samples chosen over Binance/Coinbase live capture, since LOBSTER gives paired trade+quote data; the Coinbase `level2.jsonl` capture the developer had was quote-only (order book depth, no trades) and was set aside.
- Symbols: all 5 free LOBSTER tickers (AAPL, AMZN, GOOG, INTC, MSFT), not just AAPL.
- LOBSTER level: **level 1 only** for all symbols. Deeper levels (5/10/30/50) considered and rejected, they add order-book depth activity that doesn't change top-of-book bid/ask, so they wouldn't add genuine new trade/quote rows for this schema.
- 5M row stretch goal: **dropped**. Real data caps at ~1.17M combined rows (all 5 symbols, one trading day, that's all LOBSTER's free tier offers). Rather than top up with synthetic data, the benchmark ceiling was set at ~1M rows, all real.
- Benchmark subsampling: **chronological** (first N rows), not random. Simpler to explain, preserves natural intraday clustering. Tradeoff: 10k/100k tiers skew toward the market-open period (known busiest window of the day), noted as a writeup caveat.
- PyKX bridge: **cut from scope**. Not part of the near-term build. Could be revisited later as a standalone extension, not blocking anything here.
- ML integration (e.g., feeding kdb+-sourced data into the XGBoost signal from the developer's resume): **cut from scope** for this phase. Pure Python vs kdb+ speed comparison only, for now.
- Trade classification (buy/sell labeling): **in scope**. Already have LOBSTER's ground-truth `side` column to validate against once the Python/q classification logic is written.
- Trade classification method: **simple midpoint rule** (price > midpoint → buy, price < midpoint → sell, equal → unknown), not the full Lee-Ready algorithm (which adds a tick test for trades at the midpoint). Achieves 74.80% agreement with LOBSTER ground truth on the full dataset (corrected figure, see Phase 2 entry below — an earlier unstable-sort bug had inflated this to 85.82%), in the expected range for midpoint-only classification. Noted as a known limitation, not a bug, revisit only if higher accuracy becomes a goal.
- Sort stability: `pd.DataFrame.sort_values` must use `kind="stable"` when sorting `trade`/`quote` by `time`. Default quicksort is not stable and silently reordered same-nanosecond ties away from their original CSV row order (which reflects real event sequence), corrupting the asof join for those trades. Found during Phase 2 row-for-row validation. Fixed in `python/analytics.py`'s `load_data()`.
- q float comparison tolerance: kdb+'s relational operators (`=`, `<`, `>`) apply a built-in near-equality tolerance for floats, so directly comparing `price` and `midpoint` (two independently-rounded doubles that are often 1-4 ULPs apart) falsely evaluated as equal far more often than in Python's exact IEEE754 comparison. Fixed in `q/analytics.q` by comparing the sign of `price-midpoint` instead of comparing the two floats directly — the difference-then-compare-to-0 pattern sidesteps the tolerance. Found during Phase 2 row-for-row validation.

## Open items

- **Charting library for benchmark plots**: not yet confirmed. Default assumption is `matplotlib` unless told otherwise, see roadmap.md Phase 3.
- **GitHub repo**: local git repo initialized in Phase 0, no remote configured yet. Push once a GitHub remote is created and confirmed with the developer.
## Not yet started

- Benchmark harness and plots
- README / writeup

---

## Phase 0 complete — 2026-08-18

Repo scaffolded at `kdb-vs-pandas-microstructure/` with the structure specified in `roadmap.md`: `data/` (holds `all_trades.csv`, `all_quotes.csv`, moved in from the working directory), `python/` and `q/` (placeholder files created, empty pending Phase 1/2), `results/` (empty, `.gitkeep`), plus `README.md` stub, `progress.md`, `roadmap.md`. Local git repo initialized and committed. No GitHub remote yet, not pushed.

## Phase 1 complete — 2026-08-18

`python/analytics.py` implements and validates all in-scope operations against `data/all_trades.csv` and `data/all_quotes.csv`:

- **Asof join**: `pd.merge_asof(direction="backward")` on `sym`/`time`. **0 unmatched trades out of 123,984**, matches the Phase 0 validation.
- **OHLC bars**: 5-minute buckets via `groupby("sym").resample("5min")`. 390 bars total (5 symbols x ~78 bars/day). AAPL's first bar: open=585.74 (matches the known planning-time check), high=587.80, low=584.61, close=587.21, volume=89,481.
- **VWAP** by symbol: AAPL 582.72, AMZN 222.63, GOOG 569.44, INTC 26.98, MSFT 30.50.
- **Spread metrics**: mean quoted/effective spread by symbol, e.g. AAPL quotedSpread=0.1303, effectiveSpread=0.0905; INTC/MSFT much tighter (~0.011-0.012 quoted) consistent with their lower price levels.
- **Trade classification**: simple midpoint rule, originally measured at 85.82% agreement with LOBSTER's ground-truth `side` column; corrected to **74.80%** during Phase 2 after fixing the sort-stability bug (see decisions log).

Repo pushed to GitHub (`https://github.com/Vansh-Solanki/Market-Microstructure-comparative-study-KDB-vs-Pandas-`) at `main`.

## Phase 2 complete — 2026-08-18

`q/schema.q` loads `trade`/`quote` from the same CSVs via typed `0:` (header row auto-detected, no manual skip needed) and `q/analytics.q` ports every Phase 1 operation into idiomatic q (`aj`, `xbar`, `wavg`), not a literal translation.

Two real bugs surfaced during row-for-row validation (both logged above in the decisions log) and were fixed before proceeding:
1. Python's default `sort_values` (quicksort) isn't stable, scrambling same-nanosecond trade/quote ties away from CSV order. Fixed with `kind="stable"`.
2. kdb+'s float relational operators (`=`/`</`>`) have a built-in near-equality tolerance, causing many `price`/`midpoint` pairs 1-4 ULPs apart to be misclassified as exact ties. Fixed by comparing `sign(price-midpoint)` instead of comparing the floats directly.

After both fixes, full row-for-row validation (123,984 merged trade rows, 390 OHLC bars, VWAP by symbol) shows:
- **price, bid, ask, quotedSpread, effectiveSpread, side, classifiedSide**: 0 mismatches, bit-identical between q and Python, across every row.
- **OHLC bars** (open/high/low/close/volume): 0 mismatches across all 390 bars.
- **VWAP**: differs by ~1e-13 to 1e-14 per symbol — floating-point summation-order noise between q's `wavg` and pandas' `.sum()`, not a bug (explainable per roadmap's tolerance allowance).
- **Trade classification agreement**: 74.80481% (q) vs 74.8048% (Python) — matches to displayed precision.

Correctness gate cleared. Ready for Phase 3 (benchmark harness) — not yet started.
