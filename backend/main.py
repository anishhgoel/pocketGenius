import os
import logging
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Query
from fastapi.responses import JSONResponse

from backend.config.logging_config import setup_logging

from backend.utils.redis_cache import RedisCache
from backend.utils.file_parser import parse_csv_file
from backend.models.finance_models import Transaction, Portfolio

from backend.services.openai_service import analyze_transaction
from backend.services.investment_service import InvestmentAnalyzer



load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(title="FinGenius", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pocketgenius.onrender.com"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# redis cache initialized
default_ttl = int(os.getenv("CACHE_EXPIRATION_MINUTES", "15")) * 60
redis_cache = RedisCache(default_ttl_seconds=default_ttl)


@app.get("/")
def root():
    """
    Simple welcome message and pointer to docs.
    """
    return {"message": "Welcome to FinGenius API. Go to /docs for interactive API docs."}



@app.post("/upload-transactions")
async def upload_transactions(file: UploadFile = File(...)):
    """
    Upload a CSV of transactions (description, amount, date, etc.) There is a test.cvs file in the root 
    It will be parsed, and for each transaction call OpenAI for:
      - Category
      - Budget recommendation
      - Potential savings
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    file_location = f"/tmp/{file.filename}"

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        transactions = parse_csv_file(file_location)
        analyzed = []
        for t in transactions:
            result = await analyze_transaction(t)  # from openai_service.py
            analyzed.append({
                "description": t.description,
                "amount": t.amount,
                "date": t.date, 
                "category": result.get("category"),
                "budget_recommendation": result.get("budget_recommendation"),
                "savings_potential": result.get("savings_potential")
            })
        
        return {"transactions": analyzed}
    except Exception as e:
        logger.exception(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error parsing or analyzing transactions.")


# portfolio analysis (ROI, volatility, GPT)
@app.post("/analyze-portfolio")
def analyze_portfolio(portfolio: Portfolio = Body(...)):
    """
    Basic endpoint to analyze a user's portfolio.
    Calls our 'InvestmentAnalyzer' with default risk tolerance.
    Returns total investment, ROI, volatility, Sharpe ratio, item details, GPT advice, etc.
    """
    try:
        analyzer = InvestmentAnalyzer(
            cache=redis_cache, 
            cache_ttl_minutes=int(os.getenv("CACHE_EXPIRATION_MINUTES", "15"))
        )
        results = analyzer.analyze_portfolio(portfolio)
        return JSONResponse(content=results)
    except Exception as e:
        logger.exception(f"Error analyzing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


#  Risk Tolerance for Analysis
@app.post("/analyze-portfolio-advanced")
def analyze_portfolio_advanced(
    portfolio: Portfolio = Body(...),
    risk_tolerance: str = Query("moderate", description="conservative, moderate, or aggressive")
):
    """
    Similar to /analyze-portfolio but user can pass a custom risk_tolerance as a query param.
    E.g. POST /analyze-portfolio-advanced?risk_tolerance=aggressive
    """
    try:
        analyzer = InvestmentAnalyzer(
            cache=redis_cache,
            cache_ttl_minutes=int(os.getenv("CACHE_EXPIRATION_MINUTES", "15")),
            risk_tolerance=risk_tolerance
        )
        results = analyzer.analyze_portfolio(portfolio)
        return JSONResponse(content=results)
    except Exception as e:
        logger.exception(f"Error analyzing portfolio advanced: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# sector breakdown
@app.post("/portfolio-sector-breakdown")
def portfolio_sector_breakdown(portfolio: Portfolio = Body(...)):
    """
    Returns only the sector breakdown of the portfolio,
    skipping GPT calls and advanced metrics for speed.
    """
    try:
        analyzer = InvestmentAnalyzer(cache=redis_cache)
        # Minimal usage: fetch today's data for each symbol
        symbols = list({item.symbol.upper() for item in portfolio.items})
        today_data, _ = analyzer._fetch_market_data(symbols)

        # Build item details enough to get 'sector' + 'current_value'
        item_details = []
        for item in portfolio.items:
            sym = item.symbol.upper()
            current_price = today_data.get(sym, 0.0)
            current_val = current_price * item.quantity
            fundamentals = analyzer._fetch_fundamentals(sym)
            item_details.append({
                "symbol": sym,
                "current_value": current_val,
                "sector": fundamentals.get("sector", "Unknown"),
            })

        sector_breakdown = analyzer._calculate_sector_breakdown(item_details)
        return JSONResponse(content={"sector_breakdown": sector_breakdown})
    except Exception as e:
        logger.exception(f"Error computing sector breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# single symbol analysis

@app.post("/analyze-symbol")
def analyze_symbol(
    symbol: str = Body(..., example="AAPL"),
    purchase_price: float = Body(..., example=150.0),
    quantity: float = Body(..., example=10),
    risk_tolerance: str = Body("moderate", example="moderate")
):
    """
    Analyze a single symbol:
      - current price from yfinance
      - user purchase price/quantity => ROI
      - fundamentals => sector, PE
      - local & GPT recommendations
    """
    try:
        analyzer = InvestmentAnalyzer(
            cache=redis_cache,
            risk_tolerance=risk_tolerance
        )
        # fetch current price
        today_data, _ = analyzer._fetch_market_data([symbol.upper()])
        current_price = today_data.get(symbol.upper(), 0.0)

        invested = purchase_price * quantity
        current_val = current_price * quantity
        roi_percent = 0.0
        if invested > 0:
            roi_percent = ((current_val - invested)/invested)*100

        # fundamentals
        fundamentals = analyzer._fetch_fundamentals(symbol.upper())

        # local rec
        local_rec = analyzer._generate_symbol_recommendation(symbol.upper(), roi_percent)

        # GPT rec
        gpt_rec = analyzer._generate_symbol_recommendation_gpt(symbol.upper(), roi_percent, fundamentals)

        return {
            "symbol": symbol.upper(),
            "quantity": quantity,
            "invested_amount": invested,
            "current_price": current_price,
            "current_value": current_val,
            "roi_percent": roi_percent,
            "local_recommendation": local_rec,
            "ai_recommendation": gpt_rec,
            "fundamentals": fundamentals
        }
    except Exception as e:
        logger.exception(f"Error analyzing symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# let the  user override risk-free rate & macros
@app.post("/analyze-portfolio-custom")
def analyze_portfolio_custom(
    portfolio: Portfolio = Body(...),
    risk_free_rate: float = Body(2.0),
    macro_inflation: float = Body(3.0),
    macro_interest_rate: float = Body(5.0),
    risk_tolerance: str = Body("moderate")
):
    """
    Let the user override certain macro values or risk-free rate in the request body.
    Example JSON:
    {
      "portfolio": {
        "items": [
          { "symbol": "AAPL", "quantity": 10, "purchase_price": 150 },
          ...
        ]
      },
      "risk_free_rate": 2.0,
      "macro_inflation": 3.5,
      "macro_interest_rate": 5.0,
      "risk_tolerance": "aggressive"
    }
    """
    try:
        analyzer = InvestmentAnalyzer(
            risk_free_rate=risk_free_rate,
            cache=redis_cache,
            risk_tolerance=risk_tolerance
        )
        # Overriding the macro data method for this request
        def custom_macro_data():
            return {
                "interest_rate": macro_interest_rate,
                "inflation": macro_inflation,
                "gdp_growth": 2.1,
            }
        analyzer._fetch_macro_data = custom_macro_data  # hacky override

        results = analyzer.analyze_portfolio(portfolio)
        return JSONResponse(content=results)
    except Exception as e:
        logger.exception(f"Error analyzing portfolio with custom macros: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# macro outlook
@app.get("/macro-outlook")
def macro_outlook():
    """
    Returns some basic macro data + a GPT-summarized outlook 
    on the current environment.
    """
    try:
        analyzer = InvestmentAnalyzer(cache=redis_cache)
        macro_data = analyzer._fetch_macro_data()
        
        prompt = f"""
        You are a macroeconomic expert.
        The current environment has:
        Interest rate = {macro_data['interest_rate']}%
        Inflation = {macro_data['inflation']}%
        GDP Growth = {macro_data['gdp_growth']}%

        Provide a brief 1-2 sentence outlook on this macro situation 
        for a typical investor.
        """
        response = analyzer.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7
        )
        outlook = response.choices[0].message.content.strip()
        return {"macro_data": macro_data, "macro_outlook": outlook}
    except Exception as e:
        logger.exception(f"Error generating macro outlook: {e}")
        raise HTTPException(status_code=500, detail=str(e))