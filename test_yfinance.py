import yfinance as yf
import pandas as pd

ticker = "ETH-USD"
print(f"Fetching data for {ticker}...")

# Test 1: Info (Ticker stats)
tk = yf.Ticker(ticker)
info = tk.info
print("\n--- Ticker Info ---")
print(f"Keys found: {list(info.keys())[:10]}...")
price = info.get("regularMarketPrice", info.get("currentPrice", 0))
print(f"Current Price: {price}")

# Test 2: Download (OHLCV)
print("\n--- Downloading OHLCV (1h, 5d) ---")
df = yf.download(ticker, period="5d", interval="1h", progress=False)

print(f"DataFrame empty: {df.empty}")
if not df.empty:
    print(f"Columns: {df.columns}")
    if isinstance(df.columns, pd.MultiIndex):
        print("Handling MultiIndex columns...")
        df.columns = df.columns.get_level_values(0)
        print(f"New Columns: {df.columns}")
    print("\nRecent Data (tail 2):")
    print(df.tail(2))
