"""Python reference implementation: asof join, OHLC, VWAP, spreads, trade classification.

Source of truth the q port (Phase 2) is validated against. Run directly:
    python python/analytics.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data():
    trades = pd.read_csv(DATA_DIR / "all_trades.csv", parse_dates=["time"])
    quotes = pd.read_csv(DATA_DIR / "all_quotes.csv", parse_dates=["time"])
    # stable sort: ties at the same nanosecond must keep CSV row order (the
    # actual event sequence), default quicksort silently scrambles them
    trades = trades.sort_values("time", kind="stable").reset_index(drop=True)
    quotes = quotes.sort_values("time", kind="stable").reset_index(drop=True)
    return trades, quotes


def asof_join(trades: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge_asof(
        trades, quotes, on="time", by="sym", direction="backward"
    )
    return merged


def ohlc_bars(trades: pd.DataFrame, freq: str = "5min") -> pd.DataFrame:
    grouped = trades.set_index("time").groupby("sym")
    ohlc = grouped["price"].resample(freq).ohlc()
    volume = grouped["size"].resample(freq).sum().rename("volume")
    bars = ohlc.join(volume).dropna(subset=["open"]).reset_index()
    return bars


def vwap(trades: pd.DataFrame) -> pd.DataFrame:
    result = (
        trades.groupby("sym")
        .apply(lambda g: (g["price"] * g["size"]).sum() / g["size"].sum(), include_groups=False)
        .rename("vwap")
        .reset_index()
    )
    return result


def spread_metrics(merged: pd.DataFrame) -> pd.DataFrame:
    out = merged.copy()
    out["midpoint"] = (out["bid"] + out["ask"]) / 2
    out["quotedSpread"] = out["ask"] - out["bid"]
    out["effectiveSpread"] = 2 * (out["price"] - out["midpoint"]).abs()
    return out


def classify_trades(merged: pd.DataFrame) -> pd.DataFrame:
    out = merged.copy()
    out["classifiedSide"] = pd.Series(
        pd.NA, index=out.index, dtype="object"
    )
    out.loc[out["price"] > out["midpoint"], "classifiedSide"] = "buy"
    out.loc[out["price"] < out["midpoint"], "classifiedSide"] = "sell"
    out.loc[out["price"] == out["midpoint"], "classifiedSide"] = "unknown"
    return out


def main():
    trades, quotes = load_data()
    print(f"trades: {len(trades):,} rows, quotes: {len(quotes):,} rows")

    merged = asof_join(trades, quotes)
    unmatched = merged["bid"].isna().sum()
    print(f"asof join: {unmatched} unmatched trades out of {len(merged):,}")

    bars = ohlc_bars(trades)
    print(f"OHLC bars: {len(bars):,} rows (5min buckets x symbols)")
    aapl_open = bars[bars["sym"] == "AAPL"].iloc[0]
    print(f"AAPL first bar: open={aapl_open['open']:.2f} high={aapl_open['high']:.2f} "
          f"low={aapl_open['low']:.2f} close={aapl_open['close']:.2f} volume={aapl_open['volume']:.0f}")

    vw = vwap(trades)
    print("VWAP by symbol:")
    print(vw.to_string(index=False))

    merged = spread_metrics(merged)
    merged = classify_trades(merged)

    known = merged.dropna(subset=["side"])
    agreement = (known["classifiedSide"] == known["side"]).mean()
    print(f"Trade classification agreement with LOBSTER ground truth: {agreement:.4%}")

    print("\nSpread summary by symbol:")
    print(
        merged.groupby("sym")[["quotedSpread", "effectiveSpread"]]
        .mean()
        .round(4)
        .to_string()
    )


if __name__ == "__main__":
    main()
