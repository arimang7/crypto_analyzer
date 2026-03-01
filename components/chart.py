"""
Chart Component — Plotly candlestick chart with volume, SMA, and RSI.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def render_chart(df: pd.DataFrame, ticker: str, interval_label: str = "1시"):
    """
    Render a Plotly candlestick chart with volume subplot, SMA overlay, and RSI subplot.
    """
    if df.empty:
        st.warning("차트 데이터를 불러올 수 없습니다.")
        return

    # Create subplots: candlestick / RSI / volume
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.60, 0.20, 0.20],
        subplot_titles=None,
    )

    # --- Candlestick ---
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            increasing=dict(line=dict(color="#26a69a"), fillcolor="#26a69a"),
            decreasing=dict(line=dict(color="#ef5350"), fillcolor="#ef5350"),
            name="OHLC",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # --- SMA Overlay ---
    if "SMA" in df.columns:
        sma_data = df["SMA"].dropna()
        if not sma_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["SMA"],
                    mode="lines",
                    line=dict(color="#2962ff", width=1.5),
                    name="SMA 20",
                    showlegend=False,
                ),
                row=1, col=1,
            )

    # --- RSI ---
    if "RSI" in df.columns:
        rsi_data = df["RSI"].dropna()
        if not rsi_data.empty:
            # RSI line
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["RSI"],
                    mode="lines",
                    line=dict(color="#e040fb", width=1.5),
                    name="RSI 14",
                    showlegend=False,
                ),
                row=2, col=1,
            )
            # Overbought / Oversold zones
            fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=0.8, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=0.8, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="#363a45", line_width=0.5, row=2, col=1)

            # RSI label annotation
            last_rsi = float(rsi_data.iloc[-1])
            rsi_color = "#ef5350" if last_rsi >= 70 else "#26a69a" if last_rsi <= 30 else "#e040fb"
            fig.add_annotation(
                text=f"RSI(14): {last_rsi:.1f}",
                xref="paper", yref="y2",
                x=0.01, y=last_rsi,
                showarrow=False,
                font=dict(size=11, color=rsi_color),
            )

    # --- Volume Bars ---
    colors = [
        "#26a69a" if c >= o else "#ef5350"
        for c, o in zip(df["Close"], df["Open"])
    ]

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            marker_color=colors,
            opacity=0.7,
            name="Volume",
            showlegend=False,
        ),
        row=3, col=1,
    )

    # --- Volume SMA line ---
    vol_sma = df["Volume"].rolling(window=20).mean()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=vol_sma,
            mode="lines",
            line=dict(color="#2962ff", width=1),
            name="Vol SMA",
            showlegend=False,
        ),
        row=3, col=1,
    )

    # --- Current price annotation ---
    last_close = float(df["Close"].iloc[-1])
    last_open = float(df["Open"].iloc[-1])
    price_color = "#26a69a" if last_close >= last_open else "#ef5350"

    fig.add_hline(
        y=last_close, line_dash="dot", line_color=price_color,
        line_width=1, row=1, col=1,
    )

    # --- Layout ---
    chart_title = f"{ticker} · {interval_label}"
    last_price_str = f"시 {last_close:,.2f}"

    fig.update_layout(
        title=dict(
            text=f"<b>{chart_title}</b>  <span style='color:#787b86;font-size:12px'>{last_price_str}</span>",
            font=dict(size=14, color="#d1d4dc"),
            x=0.01,
        ),
        height=680,
        margin=dict(l=0, r=60, t=40, b=0),
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
        xaxis=dict(
            gridcolor="#1e222d", gridwidth=0.5, showgrid=True,
            rangeslider=dict(visible=False),
        ),
        xaxis2=dict(gridcolor="#1e222d", gridwidth=0.5, showgrid=True),
        xaxis3=dict(gridcolor="#1e222d", gridwidth=0.5, showgrid=True),
        yaxis=dict(
            gridcolor="#1e222d", gridwidth=0.5, showgrid=True,
            side="right", tickformat=",.2f",
            tickfont=dict(color="#787b86", size=11),
        ),
        yaxis2=dict(
            gridcolor="#1e222d", gridwidth=0.5, showgrid=True,
            side="right", range=[0, 100],
            tickvals=[30, 50, 70],
            tickfont=dict(color="#787b86", size=10),
            title=dict(text="RSI", font=dict(size=10, color="#787b86")),
        ),
        yaxis3=dict(
            gridcolor="#1e222d", gridwidth=0.5, showgrid=True,
            side="right",
            tickfont=dict(color="#787b86", size=11),
        ),
        font=dict(color="#d1d4dc"),
        hovermode="x unified",
        dragmode="pan",
    )

    # Volume SMA annotation
    vol_sma_last = vol_sma.dropna()
    if not vol_sma_last.empty:
        vol_label = f"거래량 (Volume) SMA  {vol_sma_last.iloc[-1]:,.2f}"
        fig.add_annotation(
            text=vol_label,
            xref="paper", yref="paper",
            x=0.01, y=0.17,
            showarrow=False,
            font=dict(size=11, color="#787b86"),
        )

    config = {
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["autoScale2d"],
        "displaylogo": False,
        "scrollZoom": True,
    }

    st.plotly_chart(fig, use_container_width=True, config=config)
