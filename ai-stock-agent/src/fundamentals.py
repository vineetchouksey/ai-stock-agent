import yfinance as yf

def fetch_fundamentals(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info

    return {
        "company_name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "current_price": info.get("currentPrice"),
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "operating_margin": info.get("operatingMargins"),
        "profit_margin": info.get("profitMargins")
    }
