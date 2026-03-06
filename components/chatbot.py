"""
Chatbot Component — Powered by the new google-genai SDK.
Uses streaming response with a unified architecture for Vertex and Google AI.
"""

import os
import time
import concurrent.futures
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from data.crypto_data import format_number
from data.gemini_config import get_client, get_model_id

# Available Gemini models for the chatbot dropdown
GEMINI_MODELS = {
    "⚡ gemini-flash-latest": "gemini-flash-latest",
    "✨ gemini-2.5-flash": "gemini-2.5-flash",
    "🚀 gemini-3-flash-preview": "gemini-3-flash-preview",
    "💨 gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    "🔬 gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite-preview",
}

SYSTEM_PROMPT = """당신은 전문적인 암호화폐 투자 상담사입니다. 
다음 원칙을 따르세요:

1. 기술적 분석 (이동평균선, RSI, MACD, 하모닉 패턴 등)에 기반한 전문적 분석 제공
2. 리스크 관리와 포지션 사이징에 대한 조언 포함
3. 항상 면책 조항 언급: "이 분석은 정보 제공 목적이며 투자 조언이 아닙니다"
4. 한국어로 응답
5. 간결하고 핵심적인 답변 (필요 시 표, 숫자 등 활용)
6. 현재 시장 상황에 대한 균형 잡힌 시각 유지
"""


@st.cache_data(ttl=300, show_spinner=False)
def _check_model_health() -> dict:
    """Ping all models to check latency and availability concurrently."""
    client = get_client()
    if not client:
        return {name: {"elapsed": float('inf'), "status": "🔴 Error", "model_id": m_id} for name, m_id in GEMINI_MODELS.items()}
        
    def ping_model(model_name: str, model_id: str):
        try:
            start = time.time()
            # Send a minimal prompt to measure response time
            client.models.generate_content(
                model=model_id,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.0)
            )
            elapsed = time.time() - start
            if elapsed < 1.0:
                status = "🟢 쾌적"
            elif elapsed < 3.0:
                status = "🟡 보통"
            else:
                status = "🟠 지연"
            return model_name, elapsed, status
        except Exception as e:
            return model_name, float('inf'), "🔴 혼잡"

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(GEMINI_MODELS)) as executor:
        futures = {executor.submit(ping_model, name, m_id): name for name, m_id in GEMINI_MODELS.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                name_ret, elapsed, status = future.result()
            except Exception:
                name_ret, elapsed, status = name, float('inf'), "🔴 혼잡"
            results[name_ret] = {"elapsed": elapsed, "status": status, "model_id": GEMINI_MODELS[name_ret]}
            
    return results


def render_chatbot(ticker: str = "", stats: dict = None, df: pd.DataFrame = None):
    """Render the Gemini-powered chatbot interface with streaming and timer."""
    # --- Check model health and rebuild options ---
    health_status = _check_model_health()
    
    options = []
    option_mapping = {}
    best_label = None
    best_elapsed = float('inf')

    # Ensure stable ordering
    for original_name in GEMINI_MODELS.keys():
        info = health_status.get(original_name)
        if not info:
            info = {"elapsed": float('inf'), "status": "🔴 Error", "model_id": GEMINI_MODELS[original_name]}
            
        elapsed = info["elapsed"]
        status = info["status"]
        m_id = info["model_id"]
        
        if elapsed != float('inf'):
            label = f"{original_name} ({status}, {elapsed:.1f}초)"
            if elapsed < best_elapsed:
                best_elapsed = elapsed
                best_label = label
        else:
            label = f"{original_name} ({status})"
            
        options.append(label)
        option_mapping[label] = m_id

    if not best_label and options:
        best_label = options[0]

    if "chatbot_model_label" not in st.session_state:
        st.session_state.chatbot_model_label = best_label

    # --- Header row: title + model selector ---
    header_col, model_col = st.columns([1, 2])
    with header_col:
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
    with model_col:
        current_idx = 0
        if st.session_state.chatbot_model_label in options:
            current_idx = options.index(st.session_state.chatbot_model_label)
            
        selected_label = st.selectbox(
            "모델 선택",
            options=options,
            index=current_idx,
            key="chatbot_model_selector",
            label_visibility="collapsed",
        )
        if selected_label != st.session_state.chatbot_model_label:
            st.session_state.chatbot_model_label = selected_label

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
                model_id = option_mapping.get(st.session_state.chatbot_model_label, list(option_mapping.values())[0])
                _stream_response(ticker, stats, df, model_id)
            st.session_state["chat_generating"] = False
            st.rerun()

    # Chat input
    if prompt := st.chat_input("암호화폐에 대해 질문하세요...", key="chatbot_input"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state["chat_generating"] = True
        st.rerun()


def _stream_response(ticker: str, stats: dict, df: pd.DataFrame, model_id: str = None):
    """Stream the Gemini response using the new SDK with step-by-step elapsed times."""
    prompt = st.session_state.chat_messages[-1]["content"]
    
    status_container = st.empty()
    status_container.markdown(
        f"<div style='font-size:12px; color:#787b86; padding:8px 0;'>⏳ <b>데이터 수집 중...</b></div>", 
        unsafe_allow_html=True
    )
    
    start_time = time.time()
    market_context = _build_market_context(ticker, stats, df)
    context_time = time.time()
    t_context = context_time - start_time
    
    status_container.markdown(
        f"<div style='font-size:12px; color:#787b86; padding:8px 0;'>"
        f"✅ <b>수집 완료</b> ({t_context:.1f}초) ➔ ⏳ <b>{model_id} 생각 중...</b>"
        f"</div>", 
        unsafe_allow_html=True
    )

    full_response = ""

    try:
        client = get_client()
        if not client:
            st.error("AI 클라이언트를 초기화할 수 없습니다.")
            return

        if not model_id:
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
        
        first_chunk = True
        t_first_byte = 0
        
        for chunk in chat.send_message_stream(prompt):
            if first_chunk:
                t_first_byte = time.time() - context_time
                status_container.markdown(
                    f"<div style='font-size:12px; color:#787b86; padding:8px 0;'>"
                    f"✅ <b>수집</b> ({t_context:.1f}초) ➔ ✅ <b>반응</b> ({t_first_byte:.1f}초) ➔ ⏳ <b>작성 중...</b>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                first_chunk = False

            if chunk.text:
                full_response += chunk.text
                response_placeholder.markdown(full_response)

        elapsed_total = time.time() - start_time
        t_generation = elapsed_total - t_context - t_first_byte
        
        # Final status update
        status_container.markdown(
            f"<div style='font-size:12px; color:#26a69a; padding:8px 0;'>"
            f"✅ <b>수집</b> ({t_context:.1f}초) ➔ ✅ <b>반응</b> ({t_first_byte:.1f}초) ➔ ✅ <b>작성</b> ({t_generation:.1f}초) — <b>총 {elapsed_total:.1f}초</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

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
