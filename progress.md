# Progress Log

Status tracker for the kdb+/q vs Python market microstructure project. Update this file as phases complete, don't delete history, append below each entry.

---

## Current status: Phase 3 complete (benchmark harness + charts)

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
- q `aj` needs the quote table's `sym` column tagged with the `` `p# `` (parted) attribute, on data pre-sorted sym-then-time, to use its binary-search fast path. Without it, `aj` fell back to a much slower path: **~283 seconds** for the full-dataset asof join, vs **~0.03 seconds** with the attribute set — roughly a 10,000x difference, for identical results. Found while building the Phase 3 benchmark (the slow path is why early benchmark runs looked like they were silently hanging or failing). Fixed in `q/schema.q`, which now sorts `` `sym`time `` and applies `` `p#sym `` to both tables. `q/benchmark.q`'s chronological tiering needs pure time order for its subsampling, which breaks that attribute, so its `asof_join` timing includes the cost of re-sorting and re-tagging each tiered subsample — see the caveat comment in that file.
- q parser gotcha: a line containing **only** `/` (no trailing text) toggles kdb+'s parser into multi-line block-comment mode, which is only closed by a line containing only `\`. Without a closing `\`, everything after that lone `/` is silently swallowed as a comment — no error, no output, script just does nothing. This cost significant time debugging an apparently-silent `q/benchmark.q` failure during Phase 3 before being traced to a single blank `/` separator line in a comment block. Lesson: never use a bare `/` line as a comment-block spacer in q scripts, use `/ ` (slash plus content, even just a space) or omit the separator line entirely.

## Open items

- **GitHub repo**: pushed and tracked at `https://github.com/Vansh-Solanki/Market-Microstructure-comparative-study-KDB-vs-Pandas-`, `main` branch.

## Not yet started

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

Correctness gate cleared.

## Phase 3 complete — 2026-08-18

`python/benchmark.py` and `q/benchmark.q` time asof join, OHLC, and VWAP at three chronological (first-N-rows) tiers — 10k, 100k, full (123,984 trades / 1,041,889 quotes) — and `python/benchmark.py` plots the results (`matplotlib`, confirmed as the charting library, log-log axes, one line per language) to `results/benchmark_asof_join.png`, `results/benchmark_ohlc.png`, `results/benchmark_vwap.png`. Raw numbers in `results/benchmark_python.csv` and `results/benchmark_q.csv`.

Two real findings surfaced while building this phase (both logged above in the decisions log):
1. **q's `aj` needs the `` `p# `` parted attribute** on a sym-then-time-sorted quote table for its fast path — a ~10,000x difference (283s → 0.03s) on the full dataset. Fixed in `schema.q`, which benefits Phase 2's `analytics.q` as well (same correctness, much faster).
2. **A lone `/` line silently breaks a q script** by entering block-comment mode with no closing `\`. Cost significant debugging time chasing an apparently-silent benchmark failure. Fixed by removing the bare separator line from `benchmark.q`'s header comment.

Results (seconds, full-dataset tier: 123,984 trades / 1,041,889 quotes):

| Operation | Python | q | Speedup |
|---|---|---|---|
| asof_join | 0.381 | 0.094 | ~4.1x |
| ohlc | 0.075 | 0.0043 | ~17.4x |
| vwap | 0.027 | 0.0016 | ~17.5x |

q is faster at every tier and every operation. The asof-join speedup narrows toward this scale specifically because `benchmark.q`'s timing includes the re-sort + `` `p# `` re-tag cost forced by chronological tiering (see the decisions log entry and the caveat comment in `q/benchmark.q`) — the pure-join-only cost (no re-sort) is closer to ~0.03s, i.e. ~13x, consistent with Phase 2's discovery. Also tracked: Python peak memory via `tracemalloc` (grows from ~1.5MB at 10k rows to ~78MB at full scale for asof_join); not tracked on the q side (awkward to measure per-op without external tooling, noted as a caveat per roadmap allowance).

Caveats (also documented as code comments in both benchmark scripts): in-memory only, not kdb+'s on-disk historical engine; chronological subsampling skews 10k/100k tiers toward the market-open period; idiomatic-not-literal q port; q's asof-join timing includes attribute setup cost that Python's doesn't need an equivalent for.

Ready for Phase 4 (writeup) — not yet started.
