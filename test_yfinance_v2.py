import yfinance as yf

ticker = "ETH-USD"
tk = yf.Ticker(ticker)

print("--- Testing fast_info ---")
try:
    fi = tk.fast_info
    print(f"Keys: {list(fi.keys())}")
    print(f"Last Price: {fi.get('last_price')}")
    print(f"Previous Close: {fi.get('previous_close')}")
    print(f"Day High: {fi.get('day_high')}")
    print(f"Market Cap: {fi.get('market_cap')}")
except Exception as e:
    print(f"fast_info failed: {e}")

print("\n--- Testing history (1d) ---")
h = tk.history(period="1d")
if not h.empty:
    print(f"History tail:\n{h.tail(1)}")
    # Handle columns just in case
    if isinstance(h.columns, yf.utils.pd.MultiIndex):
         print("History is MultiIndex")
    else:
         print("History matches expected")
