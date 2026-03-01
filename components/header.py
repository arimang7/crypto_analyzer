"""
Header Component — Top stats bar with crypto selector and live stats.
"""

import streamlit as st
from data.crypto_data import format_number


def render_header(selected_symbol: str, stats: dict):
    """Render the top header bar with crypto stats."""
    price = stats.get("price", 0)
    high_24h = stats.get("high_24h", 0)
    change_24h = stats.get("change_24h", 0)
    change_pct = stats.get("change_pct", 0)
    volume_24h = stats.get("volume_24h", 0)
    market_cap = stats.get("market_cap", 0)

    change_class = "positive" if change_24h >= 0 else "negative"
    change_sign = "+" if change_24h >= 0 else ""

    header_html = f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-label">마크가격</div>
            <div class="stat-value">${price:,.1f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">오라클가</div>
            <div class="stat-value">${price:,.1f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">24시간 변동</div>
            <div class="stat-value {change_class}">
                {change_sign}${abs(change_24h):,.1f} / {change_sign}{change_pct:.2f}%
            </div>
        </div>
        <div class="stat-item">
            <div class="stat-label">24시간 거래량</div>
            <div class="stat-value">{format_number(volume_24h)}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">미청산 계약수</div>
            <div class="stat-value">{format_number(market_cap)}</div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
