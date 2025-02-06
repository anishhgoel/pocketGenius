import os
import math
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional, List
from openai import OpenAI

from ..models.finance_models import Portfolio, PortfolioItem
from ..utils.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class InvestmentAnalyzer:
    """
    An Investment Analyzer that:
      1) Fetches current/historical prices from yfinance
      2) Computes:
         - ROI, volatility, Sharpe ratio
         - Per-holding fundamentals & sector data
         - Diversification breakdown
         - Correlation-based portfolio risk
      3) Uses GPT for both item-level and portfolio-level advice, 
         factoring in fundamentals, user risk tolerance, and macros.
    """

    def __init__(
        self,
        risk_free_rate: Optional[float] = None,
        cache: Optional[RedisCache] = None,
        cache_ttl_minutes: int = 15,
        risk_tolerance: str = "moderate",  # "conservative", "moderate", "aggressive"
    ):
        """
        :param risk_free_rate: e.g., 2.0 for 2%. Used for Sharpe Ratio.
        :param cache: RedisCache instance to store/fetch data for performance.
        :param cache_ttl_minutes: How long to cache data in minutes.
        :param risk_tolerance: A user-supplied risk tolerance string
                               that we can pass to the GPT prompts or logic.
        """
        if risk_free_rate is None:
            self.risk_free_rate = float(os.getenv("RISK_FREE_RATE", " 4.54"))
        else:
            self.risk_free_rate = risk_free_rate

        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_minutes * 60

        # basic risk tolerance
        self.risk_tolerance = risk_tolerance.lower().strip()

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    # MAIN ENTRY POINT
    def analyze_portfolio(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Main entry point:
         1) Fetch market data
         2) Compute ROI, volatility, Sharpe
         3) Gather fundamental + sector data
         4) Summarize diversification
         5) GPT for item-level + overall advice
        """
        logger.info("Starting portfolio analysis...")

        # Basic fetch of price data
        symbols = list({item.symbol.upper() for item in portfolio.items})
        today_data, historical_data = self._fetch_market_data(symbols)

        #  Basic ROI + volatility
        total_investment, current_value = self._calculate_values(portfolio.items, today_data)
        roi_percent = self._calculate_roi(total_investment, current_value)
        volatility = self._calculate_portfolio_volatility(portfolio.items, historical_data)
        sharpe_ratio = self._calculate_sharpe_ratio(roi_percent, volatility)

        # Item-level expansions: fundamentals, sector, item-level GPT, etc.
        item_details = self._calculate_item_details(portfolio.items, today_data)

        # Summarization of sector breakdown => diversification
        sector_breakdown = self._calculate_sector_breakdown(item_details)

        # 5. Macro data fetch
        macro_data = self._fetch_macro_data()

        # 6. GPT-based overall advice
        local_advice = self._generate_local_advice(roi_percent, volatility, sector_breakdown)
        gpt_advice = self._generate_gpt_portfolio_advice(
            roi_percent,
            volatility,
            sector_breakdown,
            item_details,
            risk_tolerance=self.risk_tolerance,
            macro_data=macro_data
        )

        #  final result
        response = {
            "holdings": item_details,
            "sector_breakdown": sector_breakdown,
            "total_investment": total_investment,
            "current_value": current_value,
            "roi_percent": roi_percent,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "local_advice": local_advice,       # short text from code-based logic
            "gpt_advice": gpt_advice,           # GPT-based portfolio-level advice
        }

        logger.info("Portfolio analysis completed.")
        return response

    # Market data
    def _fetch_market_data(self, symbols: List[str]):
        if not symbols:
            return {}, pd.DataFrame()

        cache_key_today = "today_data_" + "_".join(symbols)
        cache_key_hist = "historical_data_" + "_".join(symbols)

        today_data = self.cache.get_json(cache_key_today) if self.cache else None
        historical_data = self.cache.get_pickle(cache_key_hist) if self.cache else None

        if today_data is not None and historical_data is not None:
            logger.debug("Using cached data for %s", symbols)
            return today_data, historical_data

        # if not cached , can be fetch from y finance
        try:
            hist = yf.download(
                tickers=symbols,
                period="1mo",      # 1 month of data
                interval="1d",
                auto_adjust=True,
                threads=True
            )
            if len(symbols) == 1:
                # single symbol => DataFrame
                if not hist.empty:
                    last_close = float(hist["Close"].iloc[-1])
                else:
                    last_close = 0.0
                today_data = {symbols[0]: last_close}
            else:
                close_df = hist["Close"] if "Close" in hist.columns else pd.DataFrame()
                td = {}
                for sym in symbols:
                    if sym in close_df.columns and not close_df[sym].dropna().empty:
                        td[sym] = float(close_df[sym].dropna().iloc[-1])
                    else:
                        td[sym] = 0.0
                today_data = td

            # Cache results
            if self.cache:
                self.cache.set_json(cache_key_today, today_data, ttl=self.cache_ttl_seconds)
                self.cache.set_pickle(cache_key_hist, hist, ttl=self.cache_ttl_seconds)

            return today_data, hist
        except Exception as e:
            logger.exception("Error fetching data from yfinance: %s", e)
            return {}, pd.DataFrame()

    #  helper functions for calculations
    def _calculate_values(self, items: List[PortfolioItem], today_data: Dict[str, float]):
        total_investment = 0.0
        current_value = 0.0
        for item in items:
            invest = item.purchase_price * item.quantity
            total_investment += invest
            cur_price = today_data.get(item.symbol.upper(), 0.0)
            current_value += cur_price * item.quantity
        return total_investment, current_value

    def _calculate_roi(self, total_investment: float, current_value: float) -> float:
        if total_investment <= 0:
            return 0.0
        return ( (current_value - total_investment) / total_investment ) * 100
## might need more checks  on this calculations, but based on stack overflow, seemed good
    def _calculate_portfolio_volatility(self, items: List[PortfolioItem], historical_data: pd.DataFrame) -> float:
        """
        Weighted std dev based on daily returns & correlations among holdings.
        """
        if historical_data.empty:
            return 0.0
        try:
            close_data = historical_data["Close"] 
        except KeyError:
            return 0.0

        if isinstance(close_data, pd.Series):
            # Single symbol => convert to DF
            if items:
                col_name = items[0].symbol.upper()
            else:
                col_name = "SINGLE"
            close_df = close_data.to_frame(name=col_name)
        else:
            close_df = close_data
            # flatten multi-index columns
            if isinstance(close_df.columns, pd.MultiIndex):
                close_df.columns = close_df.columns.droplevel(0)

        close_df = close_df.dropna(axis=1, how="all")
        if close_df.empty:
            return 0.0

        daily_ret = close_df.pct_change().dropna(how='all')
        if daily_ret.empty:
            return 0.0

        cov_matrix = daily_ret.cov()
        last_prices = close_df.iloc[-1]

        #  weight vector
        symbol_value_map = {}
        total_val = 0.0
        for item in items:
            up = item.symbol.upper()
            lp = float(last_prices[up]) if up in last_prices else 0.0
            pos_val = lp * item.quantity
            symbol_value_map[up] = pos_val
            total_val += pos_val

        weights = []
        for col in cov_matrix.columns:
            upcol = col.upper()
            val = symbol_value_map.get(upcol, 0.0)
            w = val / total_val if total_val > 0 else 0.0
            weights.append(w)
        w_array = np.array(weights, dtype=float)

        daily_portfolio_var = np.dot(w_array, np.dot(cov_matrix.values, w_array))
        annual_portfolio_var = daily_portfolio_var * 252
        annual_portfolio_vol = math.sqrt(annual_portfolio_var)
        return float(annual_portfolio_vol)

    def _calculate_sharpe_ratio(self, roi_percent: float, volatility: float) -> float:
        if volatility == 0:
            return 0.0
        roi_decimal = roi_percent / 100.0
        risk_free_decimal = self.risk_free_rate / 100.0
        return (roi_decimal - risk_free_decimal) / volatility

    #  PER-ITEM DETAILS (FUNDAMENTALS, SECTOR, GPT, ETC.)
    def _calculate_item_details(
        self,
        items: List[PortfolioItem],
        today_data: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        For each holding:
         - Compute P/L, item-level ROI
         - Fetch yfinance fundamentals (sector, pe, etc.)
         - Summon GPT for item-level advice
        """
        details = []
        for item in items:
            sym = item.symbol.upper()
            current_price = today_data.get(sym, 0.0)

            # basic P/L
            invested = item.purchase_price * item.quantity
            current_val = current_price * item.quantity
            pnl = current_val - invested
            item_roi = 0.0
            if invested > 0:
                item_roi = (pnl / invested) * 100

            # fundamentals from yfinance
            fundamentals = self._fetch_fundamentals(sym)

            # quick local recommendation based on ROI
            local_reco = self._generate_symbol_recommendation(sym, item_roi)

            # GPT-based item-level advice
            ai_reco = self._generate_symbol_recommendation_gpt(sym, item_roi, fundamentals)

            # Analyst rec using yfinance  (ill use 3 month recommendation)
            analyst_rec = self._fetch_analyst_recommendation(sym)

            details.append({
                "symbol": sym,
                "quantity": item.quantity,
                "purchase_price": item.purchase_price,
                "current_price": current_price,
                "invested_amount": invested,
                "current_value": current_val,
                "pnl": pnl,
                "item_roi_percent": item_roi,
                "local_recommendation": local_reco,
                "ai_recommendation": ai_reco,
                "analyst_recommendation": analyst_rec,
                # fundamentals (like sector, pe, etc.)
                "sector": fundamentals.get("sector", "Unknown"),
                "pe_ratio": fundamentals.get("pe_ratio", None),
            })
        return details

    #  fundamentals from yfinance .info
    def _fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Attempt to fetch sector, pe ratio, etc. 
        Returns a dict: {"sector": "...", "pe_ratio": 20.5, ...}
        """
        results = {}
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info  # sometimes it's slow or incomplete
            if info:
                results["sector"] = info.get("sector", "Unknown")
                results["pe_ratio"] = info.get("trailingPE", None)
        except Exception as e:
            logger.exception(f"Error fetching fundamentals for {symbol}: {e}")
        return results

    #  local text recommendation
    def _generate_symbol_recommendation(self, symbol: str, roi: float) -> str:
        if roi < -20:
            return f"[{symbol}] Large losses. Evaluate if you should cut or hold for possible rebound."
        elif roi < 0:
            return f"[{symbol}] Mild losses. Possibly hold or rebalance."
        elif 0 <= roi < 5:
            return f"[{symbol}] Low ROI so far. Could hold or look for better returns."
        elif 5 <= roi < 20:
            return f"[{symbol}] Decent gains. Consider partial profit or hold if bullish."
        else:
            return f"[{symbol}] Strong gains! Monitor valuation and risk."

    # GPT-based item-level advice (includes fundamentals)
    def _generate_symbol_recommendation_gpt(
        self, 
        symbol: str, 
        roi: float, 
        fundamentals: Dict[str, Any]
    ) -> str:
        """
        Example: short GPT prompt with ROI + fundamentals + user risk tolerance.
        """
        sector = fundamentals.get("sector", "Unknown")
        pe = fundamentals.get("pe_ratio", None)
        pe_str = f"PE ratio of {pe}" if pe is not None else "PE ratio not available"

        prompt = f"""
        You are a financial expert. 
        The user has {symbol} with an ROI of {roi:.2f}%, in sector {sector}, with {pe_str}.
        Their risk tolerance is {self.risk_tolerance}.
        Provide a brief recommendation (1-2 sentences) about whether to buy more, hold, or sell.
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=70,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.exception(f"OpenAI item-level error for {symbol}: {e}")
            return "AI recommendation unavailable."
        

    # analyst rec from yfinance
    def _fetch_analyst_recommendation(self, symbol: str) -> str:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.recommendations

            if df is None or df.empty:
                return "No analyst data found."

            # convert columns to lowercase for easier checks
            lower_cols = [c.lower() for c in df.columns]

            if "strongbuy" in lower_cols and "buy" in lower_cols and "hold" in lower_cols:
               
                last_row = df.iloc[-1]
                period = str(last_row.get("period", "?"))
                sb = last_row.get("strongBuy", 0)
                b  = last_row.get("buy", 0)
                h  = last_row.get("hold", 0)
                s  = last_row.get("sell", 0)
                ss = last_row.get("strongSell", 0)

                # summarizing
                return (
                    f"Aggregated ratings over {period}: "
                    f"{sb} strong buys, {b} buys, {h} holds, {s} sells, {ss} strong sells."
                )

            # based on stackoverflow if there is  old format columns: e.g. 'Firm', 'To Grade', 'Action'
            elif "firm" in lower_cols and "to grade" in lower_cols and "action" in lower_cols:
                # Old style
                last_row = df.iloc[-1]
                firm = last_row.get("Firm", "UnknownFirm")
                to_grade = last_row.get("To Grade", "N/A")
                action = last_row.get("Action", "N/A")
                date_str = str(last_row.name)
                return f"Last analyst: {firm} -> {to_grade} [{action}] on {date_str}."

            else:
                # the DataFrame doesn't match either known pattern
                return "Analyst data in an unrecognized format."
        except Exception as e:
            self.logger.exception(f"Error fetching analyst recommendations for {symbol}: {e}")
            return "Error fetching analyst recommendations."
    
    
    # 4) DIVERSIFICATION & SECTOR BREAKDOWN
    def _calculate_sector_breakdown(self, item_details: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        to suummarize % allocations by sector. 
        e.g. {"Technology": 45.0, "Healthcare": 20.0, ...}
        """
        sector_map = {}
        total_value = 0.0
        for detail in item_details:
            val = detail["current_value"]
            sec = detail["sector"] or "Unknown"
            sector_map.setdefault(sec, 0.0)
            sector_map[sec] += val
            total_value += val

        breakdown = {}
        for sec, val in sector_map.items():
            pct = (val / total_value * 100) if total_value > 0 else 0.0
            breakdown[sec] = pct
        return breakdown

    #  MACRO DATA
    def _fetch_macro_data(self) -> Dict[str, Any]:
        """
        Just a placeholder. Maybe i can find some api to put in actual data
        """
        # will return static for now
        return {
            "interest_rate": 5.25,   # Fed funds
            "inflation": 3.7,       # yoy inflation
            "gdp_growth": 2.1,      # yoy
        }

    # advice local machine
    def _generate_local_advice(
        self, 
        roi_percent: float, 
        volatility: float,
        sector_breakdown: Dict[str, float]
    ) -> str:
        """
        Simple code-based logic. E.g. if you have 80% in Tech, 
        warn about concentration risk, etc.
        """
        advice = []
        # Basic ROI comment
        if roi_percent < 0:
            advice.append("Overall negative ROI. Consider rebalancing or diversifying.")
        elif roi_percent < 5:
            advice.append("Modest ROI. You might explore higher-yield opportunities if risk tolerance allows.")
        else:
            advice.append("Solid ROI! Keep monitoring market trends.")

        # check if any single sector > 50%
        for sec, pct in sector_breakdown.items():
            if pct > 50:
                advice.append(f"You have a high concentration in {sec} ({pct:.1f}%). Consider diversifying.")
        # volatility note
        if volatility > 0.3:
            advice.append(f"Portfolio volatility is relatively high ({volatility:.2f}), watch out for big swings.")

        return " ".join(advice) or "No specific local advice."

#advice by gpt
    def _generate_gpt_portfolio_advice(
        self,
        roi_percent: float,
        volatility: float,
        sector_breakdown: Dict[str, float],
        item_details: List[Dict[str, Any]],
        risk_tolerance: str,
        macro_data: Dict[str, Any]
    ) -> str:
        """
        Summarize everything for GPT:
          - Overall ROI, volatility
          - Sector breakdown
          - risk tolerance
          - macro environment
          - short prompt request
        """
        #  a text summary
        sector_text = ", ".join([f"{sec}: {pct:.1f}%" for sec, pct in sector_breakdown.items()])
        holdings_summary = ""
        for it in item_details:
            holdings_summary += (f"\n  - {it['symbol']} in {it['sector']} with ROI={it['item_roi_percent']:.2f}%")

        macro_text = (f"Interest rate={macro_data.get('interest_rate','N/A')}%, "
                      f"Inflation={macro_data.get('inflation','N/A')}%, "
                      f"GDP Growth={macro_data.get('gdp_growth','N/A')}%")

        prompt = f"""
        You are a sophisticated financial advisor.
        The user's portfolio has an overall ROI of {roi_percent:.2f}%, 
        volatility of {volatility:.2f}, 
        and a risk tolerance of '{risk_tolerance}'.
        Sector breakdown: {sector_text}
        Macro environment: {macro_text}
        Holdings details: {holdings_summary}

        Please provide a short recommendation (2-3 sentences) 
        about how to manage or rebalance this portfolio, 
        factoring in risk tolerance, potential diversification, 
        macro environment, and the sector exposures.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("OpenAI portfolio-level error: %s", e)
            return "GPT portfolio advice unavailable."