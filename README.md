# Indian Options AI

**AI-powered Options Research & Paper-Trading Platform for Indian Markets (NSE)**

> ⚠ **This is a research tool. It does NOT guarantee profit. All analysis is probabilistic.**

## Phase 1 — Real Data + Option Chain + Dashboard

### What's Included

- **Real NSE option chain data** via direct NSE API access (experimental)
- **Option chain analysis**: PCR, Max Pain, OI concentration zones, unusual activity
- **Interactive Streamlit dashboard** with Plotly charts
- **Data quality indicators**: LIVE / DELAYED / STALE / END_OF_DAY / UNAVAILABLE
- **Provider abstraction**: Easy to swap to Kite Connect, Dhan, Fyers, etc.
- **SQLite (dev) / PostgreSQL (production)** database support
- **Comprehensive test suite**

### Supported Underlyings

| Symbol | Name | Lot Size |
|--------|------|----------|
| NIFTY | NIFTY 50 | 25 |
| BANKNIFTY | BANK NIFTY | 15 |
| FINNIFTY | NIFTY Financial Services | 25 |

### Quick Start

```bash
# 1. Clone / navigate to project
cd "indian stock market ai"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env

# 4. Start the FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# 5. Start the Streamlit dashboard (new terminal)
streamlit run dashboard/app.py

# 6. Open in browser
# Dashboard: http://localhost:8501
# API docs: http://localhost:8000/docs
```

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
indian-options-ai/
├── .env.example          # Environment variable template
├── .gitignore
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # PostgreSQL service
├── config/
│   └── settings.yaml     # App configuration (underlyings, thresholds)
├── src/
│   ├── api/              # FastAPI REST API
│   ├── cache/            # Cache abstraction (in-memory, future: Redis)
│   ├── database/         # SQLAlchemy ORM, repository pattern
│   ├── ingestion/        # Data provider abstraction + NSE/yfinance
│   ├── options/          # Option chain analyzer + utilities
│   ├── preprocessing/    # Data cleaning + validation
│   └── utils/            # Config, logging, time utilities
├── dashboard/
│   ├── app.py            # Streamlit main app
│   ├── pages/            # Market overview, option chain
│   └── components/       # Charts, data quality badges
├── tests/                # pytest suite
├── data/                 # Raw/processed/cached data (gitignored)
├── models/               # Trained models (future phases)
└── notebooks/            # Jupyter notebooks (future)
```

### Architecture

```
DATA SOURCE (NSE / Broker API)
       ↓
PROVIDER ABSTRACTION (ABC interfaces)
       ↓
CLEANING + VALIDATION
       ↓
DATABASE (SQLite / PostgreSQL)
       ↓
OPTION CHAIN ANALYZER
       ↓
FastAPI REST API
       ↓
Streamlit Dashboard (Plotly charts)
```

### Key Design Decisions

1. **Provider Abstraction**: All data access is behind abstract interfaces. NSE direct access is experimental. Broker APIs (Kite, Dhan, Fyers) plug in by implementing `MarketDataProvider` / `OptionsDataProvider`.

2. **Static vs Dynamic Separation**: Option contracts (underlying, strike, expiry, lot size) are separate from timestamped observations (LTP, volume, OI, IV, Greeks). IV and Greeks are NOT stored on the contract.

3. **Probabilistic Language**: The system NEVER says "market WILL move to X". All interpretations use "potential", "may indicate", "probabilistic".

4. **NULL over Fake**: Missing data shows UNAVAILABLE — never silently invented.

5. **Data Freshness**: Dashboard clearly labels data as LIVE / DELAYED / STALE / END_OF_DAY / UNAVAILABLE.

### Database

**SQLite (default, works out of the box):**
```env
DATABASE_URL=sqlite:///./data/indian_options.db
```

**PostgreSQL (recommended for larger datasets):**
```bash
docker-compose up -d  # Starts PostgreSQL
```
```env
DATABASE_URL=postgresql+psycopg2://options_user:options_dev_password@localhost:5432/indian_options_ai
```

### Adding a New Data Provider

1. Implement `MarketDataProvider` and/or `OptionsDataProvider` from `src/ingestion/base.py`
2. Register in `src/ingestion/provider_factory.py`
3. Set `MARKET_DATA_PROVIDER=your_provider` in `.env`

### Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Real Data + Option Chain + Dashboard | ✅ Complete |
| 2 | Technical Analysis + Market Regime | ⏳ Next |
| 3 | Greeks + IV + Volatility Analysis | ⏳ Planned |
| 4 | Options Strategy Engine | ⏳ Planned |
| 5 | Backtesting | ⏳ Planned |
| 6 | ML Models | ⏳ Planned |
| 7 | AI Analyst (LLM) | ⏳ Planned |
| 8 | Paper Trading | ⏳ Planned |
| 9 | Advanced Portfolio/Risk | ⏳ Planned |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./data/indian_options.db` |
| `MARKET_DATA_PROVIDER` | Active market data provider | `nse` |
| `OPTIONS_DATA_PROVIDER` | Active options data provider | `nse` |
| `RATE_LIMIT_DELAY_SECONDS` | Min seconds between API requests | `2.0` |
| `CACHE_TTL_LIVE_SECONDS` | Cache TTL during market hours | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RISK_FREE_RATE` | Annualized risk-free rate | `0.07` |

### License

Private — for personal research use only.
