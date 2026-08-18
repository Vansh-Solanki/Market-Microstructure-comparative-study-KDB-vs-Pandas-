# Progress Log

Status tracker for the kdb+/q vs Python market microstructure project. Update this file as phases complete, don't delete history, append below each entry.

---

## Current status: Phase 0 complete (repo scaffold in place)

## Environment

- **q/kdb+**: installed and working on the developer's machine, verified. Note: as of Phase 0, `q` was not found on the Windows PATH nor inside the WSL Ubuntu distro checked (`docker-desktop` and `Ubuntu` are the two WSL distros present, Ubuntu has no `q` installed). Running the q port will require either installing kdb+ inside WSL, or a native Windows q install with its location added to PATH. Flagged here, not yet resolved.
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

## Open items

- **Charting library for benchmark plots**: not yet confirmed. Default assumption is `matplotlib` unless told otherwise, see roadmap.md Phase 3.
- **GitHub repo**: local git repo initialized in Phase 0, no remote configured yet. Push once a GitHub remote is created and confirmed with the developer.
- **q runtime access**: see Environment note above, need WSL install or native Windows install confirmed before Phase 2 can be executed.

## Not yet started

- Python reference implementation (asof join, OHLC, VWAP, spreads, trade classification)
- q/kdb+ port
- Row-for-row validation between Python and q outputs
- Benchmark harness and plots
- README / writeup

---

## Phase 0 complete — 2026-08-18

Repo scaffolded at `kdb-vs-pandas-microstructure/` with the structure specified in `roadmap.md`: `data/` (holds `all_trades.csv`, `all_quotes.csv`, moved in from the working directory), `python/` and `q/` (placeholder files created, empty pending Phase 1/2), `results/` (empty, `.gitkeep`), plus `README.md` stub, `progress.md`, `roadmap.md`. Local git repo initialized and committed. No GitHub remote yet, not pushed.
