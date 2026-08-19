/ Benchmark harness: times asof join, OHLC, and VWAP at three chronological
/ row-count tiers (10k, 100k, full), same tiers as python/benchmark.py.
/ Run from the repo root, e.g.: q q/benchmark.q
/ Caveats:
/ - In-memory only (not kdb+'s on-disk historical engine).
/ - Chronological (first-N-rows) subsampling skews 10k/100k tiers toward the
/   market-open period. Trade/quote tables are truncated to the same N
/   independently, so a handful of trades may fall outside the truncated
/   quote table's time range at small tiers.
/ - schema.q's global trade/quote tables are pre-sorted sym-then-time with a
/   `p#sym` attribute (needed for aj's binary-search fast path: without it,
/   aj on the full dataset takes ~280s instead of ~0.03s). Chronological
/   tiering here needs a pure time order, which breaks that attribute, so
/   the asof_join timing below includes the cost of re-sorting sym-then-time
/   and re-tagging `p#sym` on each tiered subsample, not just the aj call
/   itself. That setup cost is the realistic price of using aj correctly on
/   a chronologically-arriving slice, and dominates the pure-join time at
/   these row counts. Python's merge_asof needs no equivalent re-sort since
/   pandas has no analogous attribute mechanism to lose.
/ - Peak memory isn't tracked here (awkward to measure per-op in q without
/   external tooling); python/benchmark.py tracks it on the python side only.

\l q/schema.q

/ pure time order for chronological tiering (independent of the sym-grouped,
/ `p#`-tagged global trade/quote tables schema.q sets up for normal use)
tradeChrono:`time xasc trade
quoteChrono:`time xasc quote

asofJoin:{[t;q]
  tt:`sym`time xasc t;
  qq:update `p#sym from `sym`time xasc q;
  aj[`sym`time; tt; qq]}
ohlcOp:{[t] select open:first price, high:max price, low:min price, close:last price, volume:sum size
  by sym, bucket:5 xbar time.minute from t}
vwapOp:{[t] select vwap:size wavg price by sym from t}

timeIt:{[f;args]
  st:.z.p;
  r:f . args;
  et:.z.p;
  1e-9*"j"$et-st}

benchTier:{[n]
  tSub:$[null n; tradeChrono; n#tradeChrono];
  qSub:$[null n; quoteChrono; n#quoteChrono];
  tradeN:count tSub;
  ajSecs:timeIt[asofJoin;(tSub;qSub)];
  ohlcSecs:timeIt[ohlcOp;enlist tSub];
  vwapSecs:timeIt[vwapOp;enlist tSub];
  show "tier trades=",(string tradeN)," quotes=",(string count qSub)," done";
  ([] language:`q`q`q; operation:`asof_join`ohlc`vwap; rows:3#tradeN; seconds:(ajSecs;ohlcSecs;vwapSecs))}

tiers:10000 100000 0N  / 0N sentinel = full table
resultsTable:raze benchTier each tiers

(`$"results/benchmark_q.csv") 0: csv 0: resultsTable
show resultsTable
