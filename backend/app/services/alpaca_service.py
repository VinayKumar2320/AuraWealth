import logging
from typing import Dict, Any, List
from app.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

# Alpaca-py SDK imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

logger = logging.getLogger(__name__)

class AlpacaService:
    def __init__(self):
        self.trading_client = None
        self.is_live = False
        
        if ALPACA_API_KEY and ALPACA_SECRET_KEY:
            try:
                # Initialize Alpaca Trading Client
                self.trading_client = TradingClient(
                    api_key=ALPACA_API_KEY,
                    secret_key=ALPACA_SECRET_KEY,
                    paper=True # Default to paper sandbox
                )
                self.is_live = True
                logger.info("Alpaca Trading Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca client: {e}")

    def execute_basket_order(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes fractional share market orders for the calculated basket.
        If keys are missing, simulates the order placement.
        """
        results = []
        successful_orders = 0
        
        if not self.is_live:
            logger.info("Alpaca credentials missing. Simulating sandbox trade execution...")
            for asset in allocations:
                results.append({
                    "ticker": asset["ticker"],
                    "status": "simulated_success",
                    "dollar_allocated": asset["dollar_split"],
                    "shares_purchased": asset["shares"],
                    "message": f"Successfully mock-purchased {asset['shares']} shares of {asset['ticker']} at ${asset['price']}"
                })
            return {
                "execution_mode": "mock_sandbox",
                "orders": results,
                "status": "success"
            }

        # If live credentials exist, place real paper orders
        for asset in allocations:
            ticker = asset["ticker"]
            dollar_amount = asset["dollar_split"]
            
            # Skip asset if dollar amount is less than Alpaca minimum (e.g. $1 for fractional shares)
            if dollar_amount < 1.0:
                logger.warning(f"Skipping order for {ticker}: Amount ${dollar_amount} is less than Alpaca $1 minimum limit.")
                results.append({
                    "ticker": ticker,
                    "status": "skipped",
                    "message": "Amount below $1.00 minimum for fractional share order."
                })
                continue
                
            try:
                # Build Market order specifying the dollar amount (not quantity) for fractional execution
                order_data = MarketOrderRequest(
                    symbol=ticker,
                    notional=dollar_amount, # specifying notional value routes fractional share order
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
                order = self.trading_client.submit_order(order_data)
                
                results.append({
                    "ticker": ticker,
                    "status": "placed",
                    "order_id": str(order.id),
                    "dollar_allocated": dollar_amount,
                    "message": f"Market order for ${dollar_amount} submitted successfully."
                })
                successful_orders += 1
            except Exception as e:
                logger.error(f"Alpaca failed to place order for {ticker}: {e}")
                results.append({
                    "ticker": ticker,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "execution_mode": "alpaca_paper",
            "orders": results,
            "status": "success" if successful_orders > 0 else "failed"
        }
