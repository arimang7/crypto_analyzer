"""
Simulation UI Component — Renders the trading simulation controls and status.
Updated to work with the background SimulatorManager.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
@st.cache_resource
def get_simulation_manager():
    """Get the global SimulatorManager instance."""
    from data.simulator import manager
    return manager

def render_simulation_ui(df: pd.DataFrame, ticker: str):
    """Render the Trading Simulation interface."""
    st.markdown(
        """
        <div style="font-size:18px; font-weight:700; color:#d1d4dc; 
                    padding:8px 0; margin-bottom:12px; 
                    border-bottom: 2px solid #2962ff;">
            🎢 매매 시뮬레이션 (ETH-USD)
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Use the global simulator instance from manager
    mgr = get_simulation_manager()
    sim = mgr.simulator

    # --- Setup Section (If not running) ---
    if sim is None or not sim.is_running:
        col1, col2 = st.columns([2, 1])
        with col1:
            seed = st.number_input("시드 머니 (USD)", min_value=100.0, value=1000.0, step=100.0)
        with col2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 시뮬레이션 시작", use_container_width=True, type="primary"):
                if mgr.start(seed):
                    st.success("시뮬레이션이 백그라운드에서 시작되었습니다.")
                    st.rerun()
                else:
                    st.warning("이미 시뮬레이션이 실행 중입니다.")
    
    # --- Running Section ---
    else:
        # Header Info
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("현재 잔고", f"${sim.balance:,.2f}", f"{((sim.balance - sim.seed_money) / sim.seed_money * 100):+.2f}%")
        with c2:
            status_color = "#26a69a" if sim.active_position else "#787b86"
            pos_label = sim.active_position['direction'].upper() if sim.active_position else "NONE"
            st.markdown(
                f"<div style='color:#787b86; font-size:12px;'>포지션 상태</div>"
                f"<div style='color:{status_color}; font-size:20px; font-weight:700;'>{pos_label}</div>",
                unsafe_allow_html=True
            )
        with c3:
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            if st.button("🛑 중지", use_container_width=True):
                if mgr.stop():
                    st.info("시뮬레이션이 중지되었습니다.")
                    st.rerun()

        # Active Position Details
        if sim.active_position:
            pos = sim.active_position
            st.markdown(
                f"""
                <div style="background:rgba(41,98,255,0.05); border:1px solid #2962ff40; 
                            border-radius:8px; padding:12px; margin-top:10px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        <span style="color:#787b86; font-size:12px;">진입 시간: {pos['entry_time']}</span>
                        <span style="color:#2962ff; font-weight:600;">{pos['direction'].upper()}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; text-align:center;">
                        <div>
                            <div style="color:#787b86; font-size:11px;">진입가</div>
                            <div style="color:#d1d4dc; font-weight:600;">${pos['entry_price']:,.2f}</div>
                        </div>
                        <div>
                            <div style="color:#26a69a; font-size:11px;">익절가</div>
                            <div style="color:#26a69a; font-weight:600;">${pos['tp']:,.2f}</div>
                        </div>
                        <div>
                            <div style="color:#ef5350; font-size:11px;">손절가</div>
                            <div style="color:#ef5350; font-weight:600;">${pos['sl']:,.2f}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px; font-size:11px; color:#d1d4dc;">
                        <b>근거:</b> {pos['reasoning']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("시그널 대기 중... (백그라운드에서 5분 간격 체크)")

        # Display small log history
        if sim.history:
            st.markdown("<div style='margin-top:15px; font-size:13px; font-weight:600;'>최근 거래 내역</div>", unsafe_allow_html=True)
            for h in reversed(sim.history[-3:]):
                color = "#26a69a" if h['profit'] > 0 else "#ef5350"
                st.markdown(
                    f"<div style='font-size:11px; color:#787b86; margin-bottom:4px;'>"
                    f"{h['exit_time']} | {h['direction'].upper()} | "
                    f"<b style='color:{color};'>{h['profit']:+,.2f} ({h['pnl_pct']*100:+.2f}%)</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.caption("✅ 시뮬레이션이 백그라운드에서 실행 중입니다. 브라우저를 닫아도 기록이 유지됩니다.")
        
        if st.button("🔄 상태 새로고침", use_container_width=True):
            st.rerun()

    st.markdown(
        f"""
        <div style="font-size:11px; color:#5d606b; margin-top:20px; padding:10px; 
                    background:#1a1e2e; border-radius:4px;">
            📄 기록 파일: <span style="color:#2962ff;">trading/{datetime.now().strftime('%Y%m%d')}.md</span>
        </div>
        """,
        unsafe_allow_html=True
    )
