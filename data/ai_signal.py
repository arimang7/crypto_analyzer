"""
AI Signal Module — Generates trading signals using the new google-genai SDK.
Provides long/short entry, take-profit, and stop-loss recommendations.
"""

import os
import json
import pandas as pd
from data.gemini_config import get_client, get_model_id


def generate_signals(ticker: str, df: pd.DataFrame, num_signals: int = 2) -> list[dict]:
    """
    Use Gemini to analyze price data and generate trading signals.
    
    Args:
        ticker: Crypto ticker (e.g. 'ETH-USD')
        df: OHLCV DataFrame with recent price data
        num_signals: Number of signals to generate
    
    Returns:
        List of signal dicts with keys:
        - direction: 'long' or 'short'
        - entry: float
        - take_profit: float
        - stop_loss: float
        - style: str
        - strategy: str
        - time_ago: str
    """
    if df.empty:
        return _fallback_signals(ticker, 0)
    
    # Prepare recent price summary for the AI
    recent = df.tail(24)
    current_price = float(recent["Close"].iloc[-1])
    high = float(recent["High"].max())
    low = float(recent["Low"].min())
    avg_volume = float(recent["Volume"].mean())
    
    prompt = f"""You are a professional crypto quant trader. Analyze the following {ticker} data and generate exactly {num_signals} trading signals.

Current Price: ${current_price:,.2f}
24h High: ${high:,.2f}
24h Low: ${low:,.2f}
Average Volume: {avg_volume:,.0f}

Recent OHLCV (last 10 candles):
{recent.tail(10).to_string()}

For each signal, provide:
1. direction: "long" or "short"
2. entry: entry price (float)
3. take_profit: take profit price (float)  
4. stop_loss: stop loss price (float)
5. style: trading style (e.g. "Day", "Swing")
6. strategy: strategy name (e.g. "최대 수익", "보수적")
7. reasoning: short reasoning in Korean (string)

IMPORTANT: Return ONLY a valid JSON array with {num_signals} signal objects. No markdown, no explanation.
Example: [{{"direction":"long","entry":1995.0,"take_profit":2072.0,"stop_loss":1966.0,"style":"Day","strategy":"최대 수익","reasoning":"RSI 과매도 및 지지선 확인"}}]
"""

    try:
        client = get_client()
        if not client:
            return _fallback_signals(ticker, current_price)

        model_id = get_model_id()
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        signals = json.loads(text)
        
        # Add metadata and ensure numeric types
        time_labels = ["6m ago", "1h ago", "3h ago", "6h ago"]
        for i, sig in enumerate(signals):
            sig["time_ago"] = time_labels[i % len(time_labels)]
            # Ensure numeric fields are actually numbers
            for key in ["entry", "take_profit", "stop_loss"]:
                if key in sig:
                    try:
                        sig[key] = float(sig[key])
                    except (ValueError, TypeError):
                        pass
        
        return signals
    except Exception as e:
        print(f"AI Signal generation error: {e}")
        return _fallback_signals(ticker, current_price)


def _fallback_signals(ticker: str, current_price: float) -> list[dict]:
    """Generate basic fallback signals when AI is unavailable."""
    if current_price <= 0:
        current_price = 1000.0
    
    return [
        {
            "direction": "long",
            "entry": round(current_price * 0.999, 1),
            "take_profit": round(current_price * 1.04, 1),
            "stop_loss": round(current_price * 0.985, 1),
            "style": "Day",
            "strategy": "최대 수익",
            "reasoning": "기술적 지표 결합 분석 (Fallback)",
            "time_ago": "6m ago",
        },
        {
            "direction": "short",
            "entry": round(current_price * 1.001, 1),
            "take_profit": round(current_price * 0.965, 1),
            "stop_loss": round(current_price * 1.015, 1),
            "style": "Day",
            "strategy": "최대 수익",
            "reasoning": "기술적 지표 결합 분석 (Fallback)",
            "time_ago": "1h ago",
        },
    ]
