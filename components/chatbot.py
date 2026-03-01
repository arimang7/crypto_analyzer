"""
Chatbot Component — Powered by the new google-genai SDK.
Uses streaming response with a unified architecture for Vertex and Google AI.
"""

import os
import time
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from data.crypto_data import format_number
from data.gemini_config import get_client, get_model_id

SYSTEM_PROMPT = """당신은 전문적인 암호화폐 투자 상담사입니다. 
다음 원칙을 따르세요:

1. 기술적 분석 (이동평균선, RSI, MACD, 하모닉 패턴 등)에 기반한 전문적 분석 제공
2. 리스크 관리와 포지션 사이징에 대한 조언 포함
3. 항상 면책 조항 언급: "이 분석은 정보 제공 목적이며 투자 조언이 아닙니다"
4. 한국어로 응답
5. 간결하고 핵심적인 답변 (필요 시 표, 숫자 등 활용)
6. 현재 시장 상황에 대한 균형 잡힌 시각 유지
"""


def render_chatbot(ticker: str = "", stats: dict = None, df: pd.DataFrame = None):
    """Render the Gemini-powered chatbot interface with streaming and timer."""
    st.markdown(
        """
        <div style="font-size:16px; font-weight:700; color:#d1d4dc; 
                    padding:8px 0; margin-bottom:8px; 
                    border-bottom: 1px solid #2a2e39;">
            💬 AI 투자 상담
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show current price context badge
    if stats and stats.get("price"):
        price = stats["price"]
        change = stats.get("change_24h", 0)
        change_pct = stats.get("change_pct", 0)
        rsi_val = None
        if df is not None and "RSI" in df.columns:
            rsi_data = df["RSI"].dropna()
            if not rsi_data.empty:
                rsi_val = float(rsi_data.iloc[-1])

        change_color = "#26a69a" if change >= 0 else "#ef5350"
        sign = "+" if change >= 0 else ""
        rsi_html = f" | RSI: {rsi_val:.1f}" if rsi_val else ""

        st.markdown(
            f'<div style="font-size:12px; color:#787b86; padding:4px 8px; '
            f'background:#1a1e2e; border-radius:6px; margin-bottom:8px;">'
            f'<b style="color:#d1d4dc;">{ticker}</b> '
            f'<span style="color:{change_color};">${price:,.2f} ({sign}{change_pct:.2f}%)</span>'
            f'{rsi_html}</div>',
            unsafe_allow_html=True,
        )

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! 암호화폐 투자 상담 AI입니다. 📊\n\n"
                           "차트 분석, 매매 전략, 리스크 관리 등에 대해 질문해 주세요.",
            }
        ]

    # Display chat messages in scrollable container
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Show streaming response if currently generating
        if st.session_state.get("chat_generating"):
            with st.chat_message("assistant"):
                _stream_response(ticker, stats, df)
            st.session_state["chat_generating"] = False
            st.rerun()

    # Chat input
    if prompt := st.chat_input("암호화폐에 대해 질문하세요...", key="chatbot_input"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state["chat_generating"] = True
        st.rerun()


def _stream_response(ticker: str, stats: dict, df: pd.DataFrame):
    """Stream the Gemini response using the new SDK."""
    prompt = st.session_state.chat_messages[-1]["content"]
    market_context = _build_market_context(ticker, stats, df)
    
    start_time = time.time()
    full_response = ""

    try:
        client = get_client()
        if not client:
            st.error("AI 클라이언트를 초기화할 수 없습니다.")
            return

        model_id = get_model_id()
        
        # Prepare history for the new SDK
        history = []
        for msg in st.session_state.chat_messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        # Config with system instruction
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT + "\n\n" + market_context,
            temperature=0.7,
        )

        response_placeholder = st.empty()
        
        # Create chat session and stream
        chat = client.chats.create(model=model_id, history=history, config=config)
        
        for chunk in chat.send_message_stream(prompt):
            if chunk.text:
                full_response += chunk.text
                elapsed = time.time() - start_time
                response_placeholder.markdown(
                    full_response + f"\n\n<sub style='color:#787b86;'>⏱ {elapsed:.1f}초</sub>",
                    unsafe_allow_html=True,
                )

        elapsed = time.time() - start_time
        response_placeholder.markdown(full_response)

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": full_response}
        )

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"⚠️ AI 응답 오류 ({elapsed:.1f}초): {str(e)}"
        st.markdown(error_msg)
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": error_msg}
        )


def _build_market_context(ticker: str, stats: dict, df: pd.DataFrame) -> str:
    """Build real-time market context string."""
    lines = [f"\n## 현재 실시간 시장 데이터 ({ticker})"]

    if stats and stats.get("price"):
        lines.append(f"- 현재가: ${stats['price']:,.2f}")
        lines.append(f"- 24시간 변동: ${stats.get('change_24h', 0):,.2f} ({stats.get('change_pct', 0):+.2f}%)")
        lines.append(f"- 24시간 고가: ${stats.get('high_24h', 0):,.2f}")
        lines.append(f"- 24시간 거래량: {format_number(stats.get('volume_24h', 0))}")
        lines.append(f"- 시가총액: {format_number(stats.get('market_cap', 0))}")

    if df is not None and not df.empty:
        if "RSI" in df.columns:
            rsi_data = df["RSI"].dropna()
            if not rsi_data.empty:
                lines.append(f"- RSI(14): {float(rsi_data.iloc[-1]):.1f}")
        if "SMA" in df.columns:
            sma_data = df["SMA"].dropna()
            if not sma_data.empty:
                lines.append(f"- SMA(20): ${float(sma_data.iloc[-1]):,.2f}")

        last5 = df.tail(5)
        lines.append(f"\n최근 5개 캔들 (OHLCV):\n{last5[['Open','High','Low','Close','Volume']].to_string()}")

    lines.append("\n위 데이터를 활용하여 사용자 질문에 답변하세요.")
    return "\n".join(lines)
