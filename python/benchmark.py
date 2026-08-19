"""Benchmark harness: times asof join, OHLC, and VWAP in Python at three
chronological row-count tiers (10k, 100k, full), then plots them against
the matching q results if available.

Caveats (see progress.md decisions log for the full reasoning):
- In-memory only, not testing kdb+'s on-disk historical engine.
- Chronological (first-N-rows) subsampling means the 10k/100k tiers skew
  toward the market-open period, the busiest window of the day.
- Tiers truncate trade and quote tables independently to the same N, so at
  10k/100k a handful of trades may fall outside the truncated quote
  table's time range and go unmatched in the asof join. That's expected
  and doesn't affect the timing measurement.

Run: python python/benchmark.py
"""

import time
import tracemalloc
from pathlib import Path

import pandas as pd

from analytics import load_data, asof_join, ohlc_bars, vwap

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
TIERS = [10_000, 100_000, None]  # None = full table


def tier_label(n: int, full_n: int) -> int:
    return n if n is not None else full_n


def time_op(fn, *args):
    tracemalloc.start()
    start = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def run_benchmark(trades: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for n in TIERS:
        t_sub = trades if n is None else trades.iloc[:n]
        q_sub = quotes if n is None else quotes.iloc[:n]
        trade_n = len(t_sub)

        _, dt, mem = time_op(asof_join, t_sub, q_sub)
        rows.append({"language": "python", "operation": "asof_join", "rows": trade_n, "seconds": dt, "peak_mb": mem / 1e6})

        _, dt, mem = time_op(ohlc_bars, t_sub)
        rows.append({"language": "python", "operation": "ohlc", "rows": trade_n, "seconds": dt, "peak_mb": mem / 1e6})

        _, dt, mem = time_op(vwap, t_sub)
        rows.append({"language": "python", "operation": "vwap", "rows": trade_n, "seconds": dt, "peak_mb": mem / 1e6})

        print(f"tier trades={trade_n:>7,} quotes={len(q_sub):>8,}  done")

    return pd.DataFrame(rows)


def plot_results(py_df: pd.DataFrame, q_csv: Path):
    import matplotlib.pyplot as plt

    if not q_csv.exists():
        print(f"no q results at {q_csv}, skipping charts")
        return

    q_df = pd.read_csv(q_csv)
    combined = pd.concat([py_df.assign(language="python"), q_df.assign(language="q")], ignore_index=True)

    for op in combined["operation"].unique():
        fig, ax = plt.subplots(figsize=(7, 5))
        for lang, marker in [("python", "o"), ("q", "s")]:
            sub = combined[(combined["operation"] == op) & (combined["language"] == lang)].sort_values("rows")
            if sub.empty:
                continue
            ax.plot(sub["rows"], sub["seconds"], marker=marker, label=lang)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("rows (trades)")
        ax.set_ylabel("seconds")
        ax.set_title(f"{op}: python vs q")
        ax.legend()
        ax.grid(True, which="both", alpha=0.3)
        out_path = RESULTS_DIR / f"benchmark_{op}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"saved {out_path}")


def main():
    trades, quotes = load_data()
    py_df = run_benchmark(trades, quotes)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_csv = RESULTS_DIR / "benchmark_python.csv"
    py_df.to_csv(out_csv, index=False)
    print(f"saved {out_csv}")
    print(py_df.to_string(index=False))

    plot_results(py_df, RESULTS_DIR / "benchmark_q.csv")


if __name__ == "__main__":
    main()
