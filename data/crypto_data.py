"""
Crypto Data Module — yfinance API integration.
Fetches OHLCV data, ticker stats, and computes SMA for top cryptocurrencies.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Top 10 cryptocurrencies by market cap
CRYPTO_LIST = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "SOL": "SOL-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "AVAX": "AVAX-USD",
    "DOT": "DOT-USD",
    "LINK": "LINK-USD",
}

# Interval-to-period mapping for appropriate data ranges
INTERVAL_CONFIG = {
    "1m":  {"period": "1d",  "label": "1분"},
    "3m":  {"period": "1d",  "label": "3분"},    
    "5m":  {"period": "5d",  "label": "5분"},
    "15m": {"period": "5d",  "label": "15분"},
    "1h":  {"period": "30d", "label": "1시"},
    "4h":  {"period": "60d", "label": "4시"},
    "1d":  {"period": "180d","label": "날"},
}


def get_crypto_list() -> dict:
    """Returns dict of {symbol_short: ticker_full}."""
    return CRYPTO_LIST


def get_ohlcv(ticker: str, interval: str = "1h", period: str = None) -> pd.DataFrame:
    """
    Fetch OHLCV data from yfinance. Optimized for single ticker handling.
    """
    if period is None:
        period = INTERVAL_CONFIG.get(interval, {}).get("period", "30d")
    
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, group_by="ticker")
        if df.empty:
            return pd.DataFrame()
        
        # yfinance >= 0.2.x returns MultiIndex (Ticker, Price) for single ticker too
        # e.g. MultiIndex([('ETH-USD', 'Open'), ('ETH-USD', 'High'), ...], names=['Ticker', 'Price'])
        if isinstance(df.columns, pd.MultiIndex):
            level0 = df.columns.get_level_values(0).tolist()
            level1 = df.columns.get_level_values(1).tolist()
            ohlcv = ["Open", "High", "Low", "Close", "Volume"]
            # Level 1 contains OHLCV names → use level 1
            if any(col in level1 for col in ohlcv):
                df.columns = df.columns.get_level_values(1)
            # Level 0 contains OHLCV names → use level 0
            elif any(col in level0 for col in ohlcv):
                df.columns = df.columns.get_level_values(0)
        
        # Ensure we only have the columns we want
        desired = ["Open", "High", "Low", "Close", "Volume"]
        available = [c for c in desired if c in df.columns]
        if not available:
            print(f"Warning: No OHLCV columns found. Columns were: {df.columns.tolist()}")
            return pd.DataFrame()
        
        return df[available].dropna()
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


def get_ticker_stats(ticker: str) -> dict:
    """
    Get 24h stats for a ticker. Uses fast_info for speed and robustness in cloud.
    """
    try:
        tk = yf.Ticker(ticker)
        
        # 1. Use fast_info — attributes are snake_case in yfinance >= 0.2.x
        fi = tk.fast_info
        price = getattr(fi, "last_price", None) or 0
        prev_close = getattr(fi, "previous_close", None) or 0
        high_24h = getattr(fi, "day_high", None) or 0
        volume_24h = getattr(fi, "last_volume", None) or getattr(fi, "three_month_average_volume", None) or 0
        market_cap = getattr(fi, "market_cap", None) or 0
        
        # 2. Fallback to info if fast_info returned nothing useful
        if not price or price == 0:
            try:
                info = tk.info
                price = info.get("regularMarketPrice", info.get("currentPrice", 0)) or 0
                prev_close = info.get("regularMarketPreviousClose", info.get("previousClose", price)) or 0
                high_24h = info.get("dayHigh", info.get("regularMarketDayHigh", price)) or 0
                volume_24h = info.get("volume24Hr", info.get("regularMarketVolume", volume_24h)) or 0
                market_cap = info.get("marketCap", market_cap) or 0
            except Exception as e2:
                print(f"Fallback info also failed for {ticker}: {e2}")

        change_24h = price - prev_close if prev_close else 0
        change_pct = (change_24h / prev_close * 100) if prev_close else 0
        
        return {
            "price": price,
            "high_24h": high_24h,
            "change_24h": change_24h,
            "change_pct": change_pct,
            "volume_24h": volume_24h,
            "market_cap": market_cap,
        }
    except Exception as e:
        print(f"Error fetching stats for {ticker}: {e}")
        return {
            "price": 0, "high_24h": 0, "change_24h": 0,
            "change_pct": 0, "volume_24h": 0, "market_cap": 0,
        }


def compute_sma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add SMA column to OHLCV DataFrame."""
    if not df.empty and "Close" in df.columns:
        df = df.copy()
        df["SMA"] = df["Close"].rolling(window=window).mean()
    return df


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add RSI column to OHLCV DataFrame."""
    if not df.empty and "Close" in df.columns:
        df = df.copy()
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        # Use exponential smoothing after initial SMA
        for i in range(period, len(avg_gain)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
    return df


def format_number(value: float, prefix: str = "$") -> str:
    """Format large numbers with K/M/B suffixes."""
    if value is None or value == 0:
        return f"{prefix}0"
    
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    elif abs_val >= 1_000:
        return f"{prefix}{value / 1_000:.2f}K"
    else:
        return f"{prefix}{value:,.2f}"
