# Crypto Trading Dashboard — Todo

## Planning

- [x] Read CLAUDE.md workflow guide
- [x] Analyze UI mockup image
- [x] Create implementation plan → approved

## Environment

- [x] Install packages (streamlit, plotly, yfinance, google-generativeai, python-dotenv)
- [x] Set up directory structure

## Data Layer

- [x] `data/crypto_data.py` — yfinance OHLCV, stats, SMA
- [x] `data/ai_signal.py` — Gemini signal generation

## UI Layer

- [x] `styles/custom.css` — Dark theme
- [x] `.streamlit/config.toml` — Theme config
- [x] `components/header.py` — Stats bar
- [x] `components/chart.py` — Candlestick chart
- [x] `components/sidebar_copilot.py` — Signal cards & controls
- [x] `components/chatbot.py` — Gemini chatbot
- [x] `app.py` — Main application

## Verification

- [x] Test data loading (108 rows ETH 1h)
- [x] Test chart rendering (HTTP 200)
- [x] Test AI signals (fallback OK)
- [x] Test chatbot (Gemini configured)
- [ ] Visual comparison with mockup
