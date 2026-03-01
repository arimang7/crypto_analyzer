# Crypto Trading Dashboard 📊

A professional-grade cryptocurrency trading dashboard built with Streamlit and powered by Google's Gemini AI. This application provides real-time market data, AI-driven technical analysis, and a background trading simulation environment.

## 🚀 Features

- **Real-time Market Data**: Live prices and OHLCV charts for top cryptocurrencies (BTC, ETH, SOL, etc.) via yfinance.
- **AI Copilot**: Automated technical analysis focusing on RSI and Harmonic patterns to provide Long/Short signals.
- **AI Chatbot**: An interactive investment consultant capable of analyzing current market context and providing strategic advice.
- **Trading Simulation**: A background-enabled simulation engine that executes trades based on AI signals, tracking balance and PnL.
- **Modern UI**: A sleek, TradingView-inspired dark theme with responsive layouts and micro-animations.

## 📁 Project Structure

```text
crypto_analyzer/
├── app.py                  # Main application entry point
├── components/             # UI Components
│   ├── header.py           # Top bar crypto stats
│   ├── chart.py            # Candlestick charts using Plotly
│   ├── sidebar_copilot.py  # AI signal dashboard
│   ├── chatbot.py          # Interactive AI consultation
│   └── simulation_ui.py    # Simulation controls
├── data/                   # Data & Logic Layer
│   ├── crypto_data.py      # Market data fetching (yfinance)
│   ├── gemini_config.py    # AI SDK configuration (API/Vertex)
│   ├── ai_signal.py        # Signal generation logic
│   └── simulator.py        # Background simulation manager
├── styles/                 # Styling
│   └── custom.css          # CSS for modern aesthetics
├── trading/                # Simulation logs and records
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (Sensitive)
```

## 🛠 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd crypto_analyzer
```

### 2. Set Up Environment

It is recommended to use a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory and add your credentials:

```env
GEMINI_API_KEY="your_api_key_here"        # Optional if using Vertex AI
GOOGLE_CLOUD_PROJECT="your_project_id"    # Required for Vertex AI
GEMINI_MODEL="gemini-2.0-flash"           # Model selection
```

## 📈 Usage

Start the dashboard using Streamlit:

```bash
streamlit run app.py
```

### Dashboard Interaction:

1. **Selection**: Choose your ticker and timeframe (1m to 1d) from the top-left menu.
2. **AI Copilot**: Click **"🔍 롱/숏 문의"** to generate a real-time trading signal based on current technicals.
3. **Simulation**: Navigate to the **"🎢 매매 시뮬레이션"** tab to start an automated trading session. The simulator runs in the background and logs trades in the `trading/` folder.
4. **Chat**: Use the bottom chat interface to ask specific questions about market trends or technical indicators.

## ⚠️ Disclaimer

This software is for educational and informational purposes only. Trading cryptocurrencies involves significant risk. Never trade with money you cannot afford to lose.
