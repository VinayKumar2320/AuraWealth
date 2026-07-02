import random
import time
from typing import Dict, List, Any

# Static pool details to simulate high-quality researched stock info
MOCK_METRICS = {
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "asset_class": "Equities",
        "price": 218.45,
        "rsi": 58,
        "pe_ratio": 32.4,
        "sentiment": 0.85,
        "why_buy_today": "Apple's new edge AI capabilities are driving strong pre-orders for the iPhone 17 series, offsetting recent regulatory pressure in Europe."
    },
    "MSFT": {
        "name": "Microsoft Corporation.",
        "sector": "Technology",
        "asset_class": "Equities",
        "price": 447.67,
        "rsi": 49,
        "pe_ratio": 36.1,
        "sentiment": 0.78,
        "why_buy_today": "Microsoft announced a new cloud contract with major retail banks, validating Azure's enterprise security features in high-compliance sectors."
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "asset_class": "Equities",
        "price": 124.50,
        "rsi": 71,
        "pe_ratio": 68.2,
        "sentiment": 0.92,
        "why_buy_today": "Nvidia's Blackwell chip production capacity has been fully booked for the next 12 months, signaling sustained structural demand for AI hardware."
    },
    "TSLA": {
        "name": "Tesla Inc.",
        "sector": "Consumer Cyclical",
        "asset_class": "Equities",
        "price": 198.80,
        "rsi": 62,
        "pe_ratio": 54.3,
        "sentiment": 0.65,
        "why_buy_today": "Tesla's full self-driving beta has been approved for a trial run in key European cities, boosting retail investor confidence."
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "sector": "Consumer Cyclical",
        "asset_class": "Equities",
        "price": 189.30,
        "rsi": 52,
        "pe_ratio": 41.5,
        "sentiment": 0.80,
        "why_buy_today": "Amazon's cloud sector AWS reported a 15% year-over-year revenue bump, showing robust corporate tech spending stabilization."
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "sector": "Technology",
        "asset_class": "Equities",
        "price": 504.10,
        "rsi": 56,
        "pe_ratio": 28.7,
        "sentiment": 0.74,
        "why_buy_today": "Meta's Llama-4 model is seeing rapid open-source adoption, creating an ecosystem that lowers long-term infrastructure overhead."
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "sector": "Technology",
        "asset_class": "Equities",
        "price": 178.60,
        "rsi": 45,
        "pe_ratio": 24.3,
        "sentiment": 0.71,
        "why_buy_today": "Google's search integration of AI summaries is showing higher click-through rates for ad links than early internal estimates."
    },
    "UNH": {
        "name": "UnitedHealth Group Inc.",
        "sector": "Healthcare",
        "asset_class": "Equities",
        "price": 512.40,
        "rsi": 38,
        "pe_ratio": 19.8,
        "sentiment": 0.55,
        "why_buy_today": "UnitedHealth group posts strong quarterly earnings with a lower medical loss ratio than forecasted, indicating robust cost management."
    },
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "sector": "Financial Services",
        "asset_class": "Equities",
        "price": 204.15,
        "rsi": 42,
        "pe_ratio": 11.2,
        "sentiment": 0.60,
        "why_buy_today": "JPMorgan's net interest income guidance has raised analyst expectations, showing resilience in the high-yield macro landscape."
    },
    "LLY": {
        "name": "Eli Lilly & Co.",
        "sector": "Healthcare",
        "asset_class": "Equities",
        "price": 894.20,
        "rsi": 66,
        "pe_ratio": 82.5,
        "sentiment": 0.88,
        "why_buy_today": "Eli Lilly secures a new factory expansion in Germany, accelerating GLP-1 weight loss drug shipments to international markets."
    },
    "GLD": {
        "name": "SPDR Gold Shares",
        "sector": "Precious Metals",
        "asset_class": "Precious Metals",
        "price": 234.50,
        "rsi": 50,
        "pe_ratio": 0.0,
        "sentiment": 0.80,
        "why_buy_today": "Gold prices hit record highs as inflation concerns linger and the Federal Reserve hints at interest rate cuts."
    },
    "SLV": {
        "name": "iShares Silver Trust",
        "sector": "Precious Metals",
        "asset_class": "Precious Metals",
        "price": 28.20,
        "rsi": 48,
        "pe_ratio": 0.0,
        "sentiment": 0.72,
        "why_buy_today": "Silver sees industrial demand surge in solar panel manufacturing alongside standard monetary hedging."
    },
    "USO": {
        "name": "United States Oil Fund",
        "sector": "Energy/Commodities",
        "asset_class": "Commodities",
        "price": 74.15,
        "rsi": 55,
        "pe_ratio": 0.0,
        "sentiment": 0.68,
        "why_buy_today": "Crude oil pushes higher amid production cuts in key OPEC nations and rising geopolitical risk in the Middle East."
    }
}

class MockDataService:
    def __init__(self):
        # Keep track of active price state to simulate live ticks
        self.prices = {ticker: metrics["price"] for ticker, metrics in MOCK_METRICS.items()}
        self.sentiments = {ticker: metrics["sentiment"] for ticker, metrics in MOCK_METRICS.items()}

    def get_daily_recommendations(self, risk_level: str = "moderate") -> List[Dict[str, Any]]:
        """
        Filters and ranks stocks based on risk level.
        Conservative: prefers low risk assets like Precious Metals, stable financials/healthcare
        Aggressive: prefers Equities, momentum Technology
        Moderate: balances the two
        """
        recommended = []
        for ticker, data in MOCK_METRICS.items():
            current_price = self.prices[ticker]
            sentiment = self.sentiments[ticker]
            rsi = data["rsi"]
            
            # Scoring mechanism supporting asset classes
            if risk_level == "conservative":
                # Prefers low risk: low P/E, RSI not overbought, weight precious metals & defensive sectors higher
                sector_bonus = 0.2 if data["sector"] in ["Healthcare", "Financial Services"] else 0.0
                asset_class_bonus = 0.35 if data["asset_class"] == "Precious Metals" else 0.0
                rsi_penalty = max(0, (rsi - 50) / 100)
                pe_penalty = (data["pe_ratio"] / 200) if data["pe_ratio"] > 0 else 0.0
                score = sentiment + sector_bonus + asset_class_bonus - rsi_penalty - pe_penalty
            elif risk_level == "aggressive":
                # Prefers high momentum: tech sector, high sentiment, ignores high PE, de-prioritizes commodities/metals
                sector_bonus = 0.25 if data["sector"] == "Technology" else 0.0
                asset_class_bonus = -0.15 if data["asset_class"] in ["Precious Metals", "Commodities"] else 0.0
                rsi_bonus = 0.1 if rsi > 60 else 0.0
                score = sentiment + sector_bonus + asset_class_bonus + rsi_bonus
            else:  # Moderate
                # Balanced asset class and sector scores
                asset_class_bonus = 0.15 if data["asset_class"] in ["Precious Metals", "Commodities"] else 0.0
                score = sentiment + asset_class_bonus - abs(rsi - 50) / 150
            
            recommended.append({
                "ticker": ticker,
                "name": data["name"],
                "sector": data["sector"],
                "asset_class": data["asset_class"],
                "price": round(current_price, 2),
                "rsi": rsi,
                "pe_ratio": data["pe_ratio"],
                "sentiment_score": round(sentiment, 2),
                "why_buy_today": data["why_buy_today"],
                "raw_score": score
            })
            
        # Sort by raw score descending
        recommended = sorted(recommended, key=lambda x: x["raw_score"], reverse=True)
        
        # Take between 5 and 8 stocks depending on risk
        limit = 5 if risk_level == "conservative" else (8 if risk_level == "aggressive" else 6)
        return recommended[:limit]


    def update_live_prices(self) -> Dict[str, float]:
        """
        Simulates random walk price ticks (+/- 0.05% to 0.15% per tick)
        """
        updates = {}
        for ticker in self.prices:
            change_pct = random.uniform(-0.0015, 0.0015)
            self.prices[ticker] *= (1 + change_pct)
            updates[ticker] = round(self.prices[ticker], 2)
        return updates

    def get_live_market_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns full detailed market information
        """
        res = {}
        for ticker, data in MOCK_METRICS.items():
            res[ticker] = {
                "price": round(self.prices[ticker], 2),
                "change": round(self.prices[ticker] - data["price"], 2),
                "change_pct": round(((self.prices[ticker] - data["price"]) / data["price"]) * 100, 2)
            }
        return res
