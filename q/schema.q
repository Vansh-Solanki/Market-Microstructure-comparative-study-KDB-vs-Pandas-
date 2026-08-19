/ Loads trade and quote tables from data/all_trades.csv and data/all_quotes.csv.
/ Run from the repo root (paths are relative), e.g.: q q/schema.q

trade:("PSFJS";enlist",") 0: `:data/all_trades.csv
quote:("PSFFJJ";enlist",") 0: `:data/all_quotes.csv

/ sort sym-then-time (not just time) and tag sym `p# (parted): this is what lets
/ aj use its binary-search fast path instead of an unindexed scan. Without it,
/ aj on the full dataset takes ~280s instead of ~0.03s, a ~10,000x difference,
/ for identical results (0 unmatched trades either way).
trade:`sym`time xasc trade;
quote:`sym`time xasc quote;
trade:update `p#sym from trade;
quote:update `p#sym from quote;
