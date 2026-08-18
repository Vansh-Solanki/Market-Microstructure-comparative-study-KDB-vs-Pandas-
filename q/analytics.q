/ q reference port of python/analytics.py: asof join, OHLC, VWAP, spreads, trade classification.
/ Idiomatic q (aj, xbar, wavg), not a literal translation of the pandas version.
/ Run from the repo root, e.g.: q q/analytics.q

\l q/schema.q

/ --- asof join: for each trade, the most recent quote at/before its time, per sym ---
merged:aj[`sym`time; trade; quote]

/ --- OHLC bars: 5-minute buckets per sym ---
ohlcBars:select open:first price, high:max price, low:min price, close:last price, volume:sum size
  by sym, bucket:5 xbar time.minute from trade

/ --- VWAP per sym ---
vwapBySym:select vwap:size wavg price by sym from trade

/ --- spread metrics, joined onto the merged trade/quote rows ---
merged:update midpoint:(bid+ask)%2 from merged
merged:update quotedSpread:ask-bid, effectiveSpread:2*abs price-midpoint from merged

/ --- trade classification: simple midpoint rule, matches python/analytics.py ---
/ q's =/</> on floats apply a built-in near-equality tolerance, which falsely calls
/ price and midpoint "equal" when they're just 1-4 ULPs apart from independent rounding.
/ Comparing the sign of the difference instead avoids that tolerance.
merged:update pmDiff:price-midpoint from merged
merged:update classifiedSide:?[pmDiff>0;`buy;?[pmDiff<0;`sell;`unknown]] from merged

/ --- summary output, mirrors python/analytics.py's printed sanity checks ---
unmatched:exec count i from merged where null bid
show "trades: ",(string count trade)," rows, quotes: ",(string count quote)," rows"
show "asof join: ",(string unmatched)," unmatched trades out of ",string count merged

aaplFirstBar:first select from ohlcBars where sym=`AAPL
show "AAPL first bar: ",("open=",(string aaplFirstBar`open),
  " high=",(string aaplFirstBar`high),
  " low=",(string aaplFirstBar`low),
  " close=",(string aaplFirstBar`close),
  " volume=",string aaplFirstBar`volume)

show "VWAP by symbol:"
show vwapBySym

known:select from merged where not null side
agreement:100*(exec count i from known where classifiedSide=side)%count known
show "Trade classification agreement with LOBSTER ground truth: ",(string agreement),"%"

show "Spread summary by symbol:"
show select quotedSpread:avg quotedSpread, effectiveSpread:avg effectiveSpread by sym from merged
