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


def _stats_from_ohlcv(ticker: str) -> dict:
    """
    Fallback: compute stats from 2-day daily OHLCV (works in cloud where fast_info/info may be blocked).
    """
    try:
        df = yf.download(ticker, period="2d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            lv1 = df.columns.get_level_values(1).tolist()
            lv0 = df.columns.get_level_values(0).tolist()
            df.columns = df.columns.get_level_values(1) if any(c in lv1 for c in ["Close","High","Volume"]) \
                         else df.columns.get_level_values(0)
        df = df.dropna()
        if df.empty:
            return {}
        price     = float(df["Close"].iloc[-1])
        high_24h  = float(df["High"].iloc[-1])
        volume_24h = float(df["Volume"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else price
        change_24h = price - prev_close
        change_pct = (change_24h / prev_close * 100) if prev_close else 0
        return {
            "price": price, "high_24h": high_24h,
            "change_24h": change_24h, "change_pct": change_pct,
            "volume_24h": volume_24h, "market_cap": 0,
        }
    except Exception as e:
        print(f"OHLCV fallback also failed for {ticker}: {e}")
        return {}


def get_ticker_stats(ticker: str) -> dict:
    """
    Get 24h stats for a ticker.
    Priority: fast_info → ticker.info → OHLCV-based fallback (cloud-safe).
    """
    _empty = {"price": 0, "high_24h": 0, "change_24h": 0,
              "change_pct": 0, "volume_24h": 0, "market_cap": 0}
    try:
        tk = yf.Ticker(ticker)

        # 1. fast_info (fastest, sometimes unavailable in cloud)
        fi = tk.fast_info
        price      = getattr(fi, "last_price", None) or 0
        prev_close = getattr(fi, "previous_close", None) or 0
        high_24h   = getattr(fi, "day_high", None) or 0
        volume_24h = getattr(fi, "last_volume", None) or \
                     getattr(fi, "three_month_average_volume", None) or 0
        market_cap = getattr(fi, "market_cap", None) or 0

        # 2. ticker.info fallback
        if not price:
            try:
                info       = tk.info
                price      = info.get("regularMarketPrice", info.get("currentPrice", 0)) or 0
                prev_close = info.get("regularMarketPreviousClose", info.get("previousClose", price)) or 0
                high_24h   = info.get("dayHigh", info.get("regularMarketDayHigh", price)) or 0
                volume_24h = info.get("volume24Hr", info.get("regularMarketVolume", volume_24h)) or 0
                market_cap = info.get("marketCap", market_cap) or 0
            except Exception as e2:
                print(f"ticker.info failed for {ticker}: {e2}")

        # 3. OHLCV-based fallback (always works where OHLCV download is available)
        if not price:
            fallback = _stats_from_ohlcv(ticker)
            if fallback:
                return fallback

        change_24h = price - prev_close if prev_close else 0
        change_pct = (change_24h / prev_close * 100) if prev_close else 0

        return {
            "price": price, "high_24h": high_24h,
            "change_24h": change_24h, "change_pct": change_pct,
            "volume_24h": volume_24h, "market_cap": market_cap,
        }
    except Exception as e:
        print(f"get_ticker_stats error for {ticker}: {e}")
        # Last resort — OHLCV fallback
        fallback = _stats_from_ohlcv(ticker)
        return fallback if fallback else _empty


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
