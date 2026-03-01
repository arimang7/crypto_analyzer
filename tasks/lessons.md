# Lessons Learned

## 2026-02-18 — Initial Build

### yfinance Multi-Level Columns

- **Issue**: `yf.download()` returns MultiIndex columns when downloading single ticker
- **Solution**: Flatten with `df.columns = df.columns.get_level_values(0)` before accessing columns
- **Rule**: Always check for MultiIndex after yfinance download

### Gemini JSON Parsing

- **Issue**: Gemini sometimes wraps JSON in markdown code blocks
- **Solution**: Strip ````markers before`json.loads()`
- **Rule**: Always clean AI response text before parsing
