"""
Crypto Trading Dashboard — Main Application
=============================================
Run: streamlit run app.py
"""

import streamlit as st
import os

# --- Page Config (must be first Streamlit command) ---
st.set_page_config(
    page_title="Crypto Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Load Custom CSS ---
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Imports (after page config) ---
from data.crypto_data import get_crypto_list, get_ohlcv, get_ticker_stats, compute_sma, compute_rsi, INTERVAL_CONFIG
from components.header import render_header
from components.chart import render_chart
from components.sidebar_copilot import render_copilot
from components.chatbot import render_chatbot


def main():
    """Main application entry point."""

    # --- Initialize Session State ---
    if "selected_crypto" not in st.session_state:
        st.session_state.selected_crypto = "ETH"
    if "selected_interval" not in st.session_state:
        st.session_state.selected_interval = "1h"

    crypto_list = get_crypto_list()
    symbols = list(crypto_list.keys())
    selected = st.session_state.selected_crypto
    ticker = crypto_list[selected]
    interval = st.session_state.selected_interval
    interval_label = INTERVAL_CONFIG[interval]["label"]

    # ========================================
    # PRE-LOAD DATA (shared by all columns)
    # ========================================
    @st.cache_data(ttl=120)
    def load_data(t, intv):
        df = get_ohlcv(t, interval=intv)
        df = compute_sma(df, window=20)
        df = compute_rsi(df, period=14)
        return df

    @st.cache_data(ttl=60)
    def load_stats(t):
        return get_ticker_stats(t)

    df = load_data(ticker, interval)
    stats = load_stats(ticker)

    # ========================================
    # LAYOUT: 2 columns (Main and Copilot)
    # ========================================
    col_main, col_copilot = st.columns([3.5, 1.2])

    # ============ LEFT COLUMN — (Removed Chatbot from here) ============

    # ============ CENTER COLUMN — Chart ============
    with col_main:
        sel_col, stat_col = st.columns([1, 5])

        with sel_col:
            new_selected = st.selectbox(
                "암호화폐",
                options=symbols,
                index=symbols.index(selected),
                key="crypto_selector",
                label_visibility="collapsed",
                format_func=lambda x: f"◆  {x}",
            )
            if new_selected != selected:
                st.session_state.selected_crypto = new_selected
                st.rerun()

        with stat_col:
            render_header(selected, stats)

        # --- Tabs for Chart and Simulation ---
        tab_chart, tab_sim = st.tabs(["📈 분석 차트", "🎢 매매 시뮬레이션"])
        
        with tab_chart:
            # --- Timeframe Selector ---
            intervals = list(INTERVAL_CONFIG.keys())
            labels = [INTERVAL_CONFIG[k]["label"] for k in intervals]

            tf_cols = st.columns(len(intervals) + 3)
            for i, (intv, label) in enumerate(zip(intervals, labels)):
                with tf_cols[i]:
                    is_active = intv == interval
                    if is_active:
                        st.markdown(
                            f'<div style="text-align:center; padding:4px 8px; background:#2962ff; '
                            f'border-radius:4px; color:white; font-size:13px; font-weight:600; cursor:pointer;">'
                            f'{label}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button(label, key=f"tf_{intv}", use_container_width=True):
                            st.session_state.selected_interval = intv
                            st.rerun()

            render_chart(df, ticker, interval_label)

        with tab_sim:
            from components.simulation_ui import render_simulation_ui
            # Simulation always uses ETH-USD with 5m interval for high-frequency checks
            eth_ticker = "ETH-USD"
            
            @st.cache_data(ttl=60)
            def get_sim_data():
                d = get_ohlcv(eth_ticker, interval="5m")
                d = compute_sma(d, window=20)
                d = compute_rsi(d, period=14)
                return d
            
            sim_df = get_sim_data()
            render_simulation_ui(sim_df, eth_ticker)

    # ============ RIGHT COLUMN — AI Copilot ============
    with col_copilot:
        render_copilot(df, ticker)

    # ============ BOTTOM — AI Chatbot ============
    st.markdown("---")
    render_chatbot(ticker, stats, df)


if __name__ == "__main__":
    main()
