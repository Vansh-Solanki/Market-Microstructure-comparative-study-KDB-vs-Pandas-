/ Loads trade and quote tables from data/all_trades.csv and data/all_quotes.csv.
/ Run from the repo root (paths are relative), e.g.: q q/schema.q

trade:("PSFJS";enlist",") 0: `:data/all_trades.csv
quote:("PSFFJJ";enlist",") 0: `:data/all_quotes.csv

`trade set `time xasc trade;
`quote set `time xasc quote;
