"""
Trading Simulator — Handles automated buy/sell logic and logging.
Supports background execution independent of browser sessions.
"""

import os
import time
import threading
from datetime import datetime
import pandas as pd
from data.crypto_data import get_ohlcv, compute_sma, compute_rsi
from data.ai_signal import generate_signals

LOG_DIR = "trading"

class TradingSimulator:
    def __init__(self, seed_money: float):
        self.seed_money = seed_money
        self.balance = seed_money
        self.active_position = None  # {direction, entry_price, tp, sl, size, entry_time, reasoning}
        self.history = []
        self.last_check_time = 0
        self.is_running = False
        self.ticker = "ETH-USD"
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self.is_running = True
            self._log_event(f"🚀 Simulation Started. Seed Money: ${self.seed_money:,.2f}")

    def stop(self):
        with self._lock:
            self.is_running = False
            self._log_event(f"🏁 Simulation Stopped. Final Balance: ${self.balance:,.2f}")
            self._save_summary()

    def run_step(self, current_price: float, df: pd.DataFrame):
        """
        Executed periodically by the background worker.
        """
        with self._lock:
            if not self.is_running:
                return

            now = time.time()
            
            # 1. Manage Active Position (Check TP/SL)
            if self.active_position:
                self._check_exit_conditions(current_price)
            
            # 2. Check if it's time to open a new position (every 5 mins = 300s)
            elif now - self.last_check_time >= 300:
                self._try_open_position(df)
                self.last_check_time = now

    def _check_exit_conditions(self, current_price: float):
        pos = self.active_position
        direction = pos['direction']
        entry = pos['entry_price']
        tp = pos['tp']
        sl = pos['sl']
        
        exited = False
        exit_type = ""
        
        if direction == "long":
            if current_price >= tp:
                exited = True
                exit_type = "TP (익절)"
            elif current_price <= sl:
                exited = True
                exit_type = "SL (손절)"
        else: # short
            if current_price <= tp:
                exited = True
                exit_type = "TP (익절)"
            elif current_price >= sl:
                exited = True
                exit_type = "SL (손절)"
        
        if exited:
            pnl_pct = (current_price - entry) / entry if direction == "long" else (entry - current_price) / entry
            profit = self.balance * pnl_pct
            self.balance += profit
            
            log_msg = (
                f"✅ Position Closed: {exit_type}\n"
                f"- Ticker: {self.ticker}\n"
                f"- Exit Price: ${current_price:,.2f}\n"
                f"- PnL: {pnl_pct*100:+.2f}%\n"
                f"- Profit: ${profit:,.2f}\n"
                f"- New Balance: ${self.balance:,.2f}"
            )
            self._log_event(log_msg)
            
            history_item = pos.copy()
            history_item.update({
                "exit_price": current_price,
                "exit_time": datetime.now().strftime("%H:%M:%S"),
                "exit_type": exit_type,
                "pnl_pct": pnl_pct,
                "profit": profit
            })
            self.history.append(history_item)
            self.active_position = None

    def _try_open_position(self, df: pd.DataFrame):
        self._log_event("🔍 Analyzing market for new position...")
        try:
            signals = generate_signals(self.ticker, df, num_signals=1)
            if not signals:
                return

            sig = signals[0]
            entry = float(sig['entry'])
            tp = float(sig['take_profit'])
            sl = float(sig['stop_loss'])
            direction = sig['direction']
            reasoning = sig.get('reasoning', sig.get('strategy', 'AI 전략'))

            self.active_position = {
                "direction": direction,
                "entry_price": entry,
                "tp": tp,
                "sl": sl,
                "entry_time": datetime.now().strftime("%H:%M:%S"),
                "reasoning": reasoning
            }
            
            log_msg = (
                f"📥 Position Opened: {direction.upper()}\n"
                f"- Entry: ${entry:,.2f}\n"
                f"- TP: ${tp:,.2f} | SL: ${sl:,.2f}\n"
                f"- Reasoning: {reasoning}"
            )
            self._log_event(log_msg)

        except Exception as e:
            self._log_event(f"⚠️ Error opening position: {str(e)}")

    def _log_event(self, message: str):
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = os.path.join(LOG_DIR, f"{date_str}.md")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
            
        is_new = not os.path.exists(file_path)
        with open(file_path, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# Trading Log - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"### [{timestamp}]\n{message}\n\n")
        print(f"[Simulator] [{timestamp}] {message}")

    def _save_summary(self):
        log_msg = (
            f"📊 **Simulation Summary**\n"
            f"- Total Trades: {len(self.history)}\n"
            f"- Initial Balance: ${self.seed_money:,.2f}\n"
            f"- Final Balance: ${self.balance:,.2f}\n"
            f"- Total Return: {((self.balance - self.seed_money) / self.seed_money * 100):+.2f}%"
        )
        self._log_event(log_msg)

class SimulatorManager:
    """Manages a single background simulator instance (Singleton)."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SimulatorManager, cls).__new__(cls)
                cls._instance.simulator = None
                cls._instance.thread = None
                cls._instance._stop_event = threading.Event()
            return cls._instance

    def start(self, seed_money: float):
        with self._lock:
            if self.simulator and self.simulator.is_running:
                return False
            
            self.simulator = TradingSimulator(seed_money)
            self.simulator.start()
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            return True

    def stop(self):
        with self._lock:
            if self.simulator:
                self.simulator.stop()
                self._stop_event.set()
                return True
            return False

    def _worker(self):
        """Background loop."""
        print("[SimulatorManager] Background worker started.")
        while not self._stop_event.is_set():
            try:
                # 1. Fetch data
                ticker = self.simulator.ticker
                df = get_ohlcv(ticker, interval="5m")
                if not df.empty:
                    df = compute_sma(df, window=20)
                    df = compute_rsi(df, period=14)
                    current_price = float(df['Close'].iloc[-1])
                    
                    # 2. Run simulation step
                    self.simulator.run_step(current_price, df)
                
            except Exception as e:
                print(f"[SimulatorManager] Worker Error: {e}")
            
            # Wait 30 seconds before next check (TP/SL check frequency)
            time.sleep(30)
        print("[SimulatorManager] Background worker stopped.")

# Global singleton instance
manager = SimulatorManager()
