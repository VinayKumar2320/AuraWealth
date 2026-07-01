import asyncio
import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import PORT, HOST
from app.services.mock_data_service import MockDataService
from app.services.allocation_service import AllocationService
from app.services.alpaca_service import AlpacaService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Micro-Investing Allocator & Research API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
mock_data_service = MockDataService()
allocation_service = AllocationService()
alpaca_service = AlpacaService()


# In-memory websocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Handle connection issues gracefully
                logger.error(f"Error sending message to client: {e}")

manager = ConnectionManager()

# Background task to stream live price updates to web clients
async def price_streaming_task():
    logger.info("Starting live price streaming task...")
    while True:
        try:
            # Simulate real-time stock ticks
            price_updates = mock_data_service.update_live_prices()
            market_data = mock_data_service.get_live_market_data()
            
            # Broadcast updates to all connected clients
            if manager.active_connections:
                await manager.broadcast({
                    "type": "price_update",
                    "prices": price_updates,
                    "market_data": market_data
                })
        except Exception as e:
            logger.error(f"Error in price streaming task: {e}")
        
        await asyncio.sleep(1.5)  # Update prices every 1.5 seconds

@app.on_event("startup")
async def startup_event():
    # Start the background price generator
    asyncio.create_task(price_streaming_task())

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Micro-Investing Allocator API"}

@app.get("/api/recommendations")
def get_recommendations(risk_level: str = "moderate"):
    """
    Returns the daily researched picks filtered by risk profile.
    """
    recommendations = mock_data_service.get_daily_recommendations(risk_level)
    return {
        "risk_level": risk_level,
        "count": len(recommendations),
        "stocks": recommendations
    }

class AllocateRequest(BaseModel):
    amount: float
    risk_level: str = "moderate"

@app.post("/api/allocate")
def allocate_portfolio(req: AllocateRequest):
    """
    Takes an investment amount and calculates the fractional share distribution.
    """
    stocks = mock_data_service.get_daily_recommendations(req.risk_level)
    allocation = allocation_service.calculate_allocation(req.amount, stocks)
    return {
        "amount": req.amount,
        "risk_level": req.risk_level,
        **allocation
    }

class InvestAllocationItem(BaseModel):
    ticker: str
    price: float
    dollar_split: float
    shares: float

class InvestRequest(BaseModel):
    allocations: List[InvestAllocationItem]

@app.post("/api/invest")
def invest_portfolio(req: InvestRequest):
    """
    Executes a portfolio basket split trade via Alpaca API paper trading.
    """
    basket = []
    for item in req.allocations:
        basket.append({
            "ticker": item.ticker,
            "price": item.price,
            "dollar_split": item.dollar_split,
            "shares": item.shares
        })
    result = alpaca_service.execute_basket_order(basket)
    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial prices upon connection
        market_data = mock_data_service.get_live_market_data()
        await websocket.send_json({
            "type": "initial_data",
            "market_data": market_data
        })
        
        # Keep connection open and listen for optional messages (ping/config)
        while True:
            data = await websocket.receive_text()
            # If client sends a ping, return pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
