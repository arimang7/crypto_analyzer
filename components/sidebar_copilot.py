"""
AI Copilot Sidebar — Signal cards, trading controls, and RSI/Harmonic analysis.
All signals generated on-demand via the 롱/숏 문의 button with live timer.
Powered by the new google-genai SDK.
"""

import os
import re
import json
import time
import streamlit as st
import pandas as pd
from google.genai import types
from data.gemini_config import get_client

# Fast model for signal analysis
SIGNAL_MODEL = "gemini-2.5-flash-lite"


def render_copilot(df: pd.DataFrame = None, ticker: str = ""):
    """Render the AI Copilot sidebar."""
    tab_copilot, tab_autopilot = st.tabs(["🤖 AI Copilot", "🔥 Autopilot"])

    with tab_copilot:
        if "copilot_signals" in st.session_state and st.session_state["copilot_signals"]:
            _render_signal_cards(st.session_state["copilot_signals"])

        st.markdown("---")
        _render_controls(df, ticker)

    with tab_autopilot:
        st.markdown(
            """
            <div style="text-align:center; padding:40px 20px; color:#787b86;">
                <div style="font-size:40px; margin-bottom:12px;">🔥</div>
                <div style="font-size:14px; font-weight:600; color:#d1d4dc; margin-bottom:8px;">
                    Autopilot 모드
                </div>
                <div style="font-size:12px;">
                    자동 매매 기능은 준비 중입니다.<br/>
                    AI Copilot 탭에서 수동 시그널을 확인하세요.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_signal_cards(signals: list[dict]):
    """Render individual signal cards."""
    for sig in signals:
        direction = sig.get("direction", "long")
        is_long = direction.lower() == "long"

        try:
            entry = float(sig.get("entry", 0))
            tp = float(sig.get("take_profit", sig.get("target", 0)))
            sl = float(sig.get("stop_loss", 0))
        except (ValueError, TypeError):
            entry, tp, sl = 0.0, 0.0, 0.0

        style = sig.get("style", "Day")
        strategy = sig.get("strategy", "최대 수익")
        time_ago = sig.get("time_ago", "")
        pattern = sig.get("pattern", "")
        rsi_analysis = sig.get("rsi_analysis", "")
        confidence = sig.get("confidence", "")
        reasoning = sig.get("reasoning", "")

        dir_label = "롱" if is_long else "숏"
        dir_color = "#26a69a" if is_long else "#ef5350"
        dir_bg = "rgba(38,166,154,0.08)" if is_long else "rgba(239,83,80,0.08)"
        entry_class = "entry-long" if is_long else "entry-short"
        label_class = "long" if is_long else "short"
        conf_color = {"High": "#26a69a", "Medium": "#ff9800", "Low": "#ef5350"}.get(confidence, "#787b86")

        extra_rows = []
        
        # Calculate Risk/Reward Ratio Score (0 ~ 100)
        score_html = ""
        if entry > 0 and tp > 0 and sl > 0:
            reward = abs(tp - entry)
            risk = abs(sl - entry)
            if risk > 0:
                ratio = reward / risk
                # Map ratio to 0-100 score: 
                # Ratio of 1.0 (1:1) -> 50, Ratio of 2.0 (1:2) -> 75, Ratio near 0 -> 0
                score = min(100, int((ratio / (ratio + 1)) * 100))
            else:
                score = 100 if reward > 0 else 0
                ratio = float('inf')
            
            score_color = "#26a69a" if score >= 60 else "#ff9800" if score >= 40 else "#ef5350"
            score_html = f"""
            <div style="margin-top:12px; margin-bottom:4px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                    <span style="color:#787b86;">손익비 점수 (R/R: {ratio:.1f})</span>
                    <strong style="color:{score_color};">{score}점</strong>
                </div>
                <div style="width:100%; height:4px; background:rgba(255,255,255,0.1); border-radius:2px; overflow:hidden;">
                    <div style="width:{score}%; height:100%; background:{score_color}; border-radius:2px;"></div>
                </div>
            </div>
            """

        if pattern:
            extra_rows.append(f'<div style="color:#787b86;">🔷 패턴: <b style="color:#d1d4dc;">{pattern}</b></div>')
        if rsi_analysis:
            extra_rows.append(f'<div style="color:#787b86;">📊 RSI: <b style="color:#d1d4dc;">{rsi_analysis}</b></div>')
        if confidence:
            extra_rows.append(f'<div style="color:#787b86; margin-top:4px;">신뢰도: <b style="color:{conf_color};">{confidence}</b></div>')
        if reasoning:
            extra_rows.append(f'<div style="color:#9e9e9e; margin-top:4px; line-height:1.4;">{reasoning}</div>')

        extra_html = ""
        if extra_rows or score_html:
            extra_html = '<div style="margin-top:8px; padding-top:8px; border-top:1px solid #2a2e39; font-size:11px;">'
            if score_html:
                extra_html += score_html + '<div style="margin-bottom:8px;"></div>'
            extra_html += "".join(extra_rows) + '</div>'

        card_html = f"""
        <div class="signal-card" style="background:{dir_bg}; border-color:{dir_color}40;">
            <div class="signal-card-header">
                <div class="time-badge">
                    <span class="badge-icon">📊</span>
                    <span>🤖 {time_ago}</span>
                </div>
                <span>👁</span>
            </div>
            <div style="text-align:center; font-size:14px; font-weight:700; color:{dir_color}; margin-bottom:8px;">
                {"📈" if is_long else "📉"} {dir_label}
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:12px; color:#787b86;">
                <span>스타일: <b style="color:#d1d4dc;">{style}</b></span>
                <span>전략: <b style="color:#d1d4dc;">{strategy}</b></span>
            </div>
            <div class="signal-row">
                <span class="label {label_class}">{dir_label} 진입가</span>
                <span class="value {entry_class}">${entry:,.1f}</span>
            </div>
            <div class="signal-row">
                <span class="label" style="color:#26a69a;">익절</span>
                <span class="value" style="color:#26a69a;">${tp:,.1f}</span>
            </div>
            <div class="signal-row">
                <span class="label" style="color:#ef5350;">손절</span>
                <span class="value" style="color:#ef5350;">${sl:,.1f}</span>
            </div>
            {extra_html}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


def _render_controls(df: pd.DataFrame = None, ticker: str = ""):
    """Render bottom controls and 롱/숏 문의 button with live timer."""
    c1, c2, c3 = st.columns(3)

    with c1:
        st.text_input("초기 마진", value="$1000", key="initial_margin", label_visibility="visible")
    with c2:
        style = st.selectbox("스타일", options=["Day", "Swing", "Scalp", "Position"], key="style_select", label_visibility="visible")
    with c3:
        strategy = st.selectbox("전략", options=["최대 수익", "보수적", "균형", "공격적"], key="strategy_select", label_visibility="visible")

    if st.button("🔍 롱/숏 문의", key="inquiry_btn", use_container_width=True, type="primary"):
        if df is not None and not df.empty:
            start_time = time.time()
            with st.status("🔍 AI 분석 중...", expanded=True) as status:
                st.write("⏳ 하모닉 패턴 & RSI 분석 시작...")
                result = _analyze_with_harmonic_rsi(df, ticker, style, strategy)
                
                # Cleanup: sometimes genai returns results wrapped in a list
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]

                elapsed = time.time() - start_time
                st.write(f"✅ 분석 완료! ({elapsed:.1f}초)")
                status.update(label=f"✅ 분석 완료 ({elapsed:.1f}초)", state="complete")

            if isinstance(result, dict) and result:
                result["time_ago"] = f"{elapsed:.1f}초"
                result["style"] = style
                result["strategy"] = strategy
                st.session_state["copilot_signals"] = [result]
                st.session_state["analysis_elapsed"] = elapsed
                st.rerun()
        else:
            st.warning("데이터를 먼저 로딩하세요.")

    if "analysis_elapsed" in st.session_state:
        el = st.session_state["analysis_elapsed"]
        st.markdown(
            f'<div style="text-align:center; color:#787b86; font-size:11px; margin-top:4px;">'
            f'⏱ 분석 소요시간: {el:.1f}초</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="disclaimer">⚠️ 이 서비스는 투자 조언이 아닙니다. 투자 판단은 본인의 책임입니다.</div>',
        unsafe_allow_html=True,
    )


def _analyze_with_harmonic_rsi(df: pd.DataFrame, ticker: str, style: str, strategy: str) -> dict:
    """Analyze using RSI + harmonic patterns using the new genai SDK."""
    recent = df.tail(20)
    cp = float(recent["Close"].iloc[-1])
    hi = float(recent["High"].max())
    lo = float(recent["Low"].min())

    rsi_val = None
    if "RSI" in recent.columns:
        rsi_data = recent["RSI"].dropna()
        if not rsi_data.empty:
            rsi_val = float(rsi_data.iloc[-1])

    last5 = recent.tail(5)
    ohlc_lines = []
    for _, row in last5.iterrows():
        ohlc_lines.append(f"O:{float(row['Open']):.1f} H:{float(row['High']):.1f} L:{float(row['Low']):.1f} C:{float(row['Close']):.1f}")
    ohlc_str = " | ".join(ohlc_lines)

    prompt = f"""Crypto signal for {ticker}. Price:${cp:.1f} High:${hi:.1f} Low:${lo:.1f} RSI:{f'{rsi_val:.1f}' if rsi_val else 'N/A'} Style:{style} Strategy:{strategy}
Recent: {ohlc_str}
Analyze harmonic patterns and RSI. Reply JSON only: direction(long/short), pattern(name or None), rsi_analysis(Korean), entry(number), target(number), stop_loss(number), confidence(High/Medium/Low), reasoning(Korean short)"""

    try:
        client = get_client()
        if not client:
            return _fallback_result(cp, rsi_val, "Client initialization failed")

        response = client.models.generate_content(
            model=SIGNAL_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=512,
                temperature=0.2,
            ),
        )

        text = response.text.strip()
        result = json.loads(text)
        
        # Defensive casting for numeric fields if it's a dict
        if isinstance(result, dict):
            for key in ["entry", "target", "stop_loss"]:
                if key in result:
                    try:
                        result[key] = float(result[key])
                    except (ValueError, TypeError):
                        pass
        elif isinstance(result, list) and len(result) > 0:
            res = result[0]
            for key in ["entry", "target", "stop_loss"]:
                if key in res:
                    try:
                        res[key] = float(res[key])
                    except (ValueError, TypeError):
                        pass
            return res

        return result
    except json.JSONDecodeError:
        text = response.text.strip() if 'response' in locals() and response.text else ""
        return _try_parse_json(text, cp, rsi_val)
    except Exception as e:
        return _fallback_result(cp, rsi_val, str(e))


def _try_parse_json(text: str, price: float, rsi_val: float = None) -> dict:
    """Attempt to extract valid JSON from malformed response."""
    text = re.sub(r'^```\w*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    text = text.strip()

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return _fallback_result(price, rsi_val, "JSON parsing failed")


def _fallback_result(price: float, rsi_val: float = None, error: str = "") -> dict:
    """Generate fallback result when AI fails."""
    is_long = rsi_val and rsi_val < 50
    return {
        "direction": "long" if is_long else "short",
        "pattern": "N/A",
        "rsi_analysis": f"RSI {rsi_val:.1f} - {'과매도 구간' if rsi_val and rsi_val < 30 else '과매수 구간' if rsi_val and rsi_val > 70 else '중립'}" if rsi_val else "N/A",
        "entry": round(price, 1),
        "target": round(price * (1.03 if is_long else 0.97), 1),
        "stop_loss": round(price * (0.98 if is_long else 1.02), 1),
        "confidence": "Low",
        "reasoning": f"자동 분석 ({error})" if error else "RSI 기반 기본 분석",
    }
