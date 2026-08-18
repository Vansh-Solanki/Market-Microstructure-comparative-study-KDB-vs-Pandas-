# kdb+/q vs Python: Market Microstructure Benchmark

A tick-data analytics engine implemented twice — once in Python (pandas) and once in kdb+/q — over real NASDAQ trade/quote data (LOBSTER samples, AAPL/AMZN/GOOG/INTC/MSFT, 2012-06-21). Implements asof joins, OHLC bar aggregation, VWAP, spread metrics, and trade classification, then benchmarks the two implementations against each other.

**Status: work in progress.** See `progress.md` for current status and `roadmap.md` for the phased build plan.
