"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";

interface AllocationItem {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  sentiment_score: number;
  why_buy_today: string;
  allocation_pct: number;
  dollar_split: number;
  shares: number;
}

interface PortfolioData {
  total_allocated: number;
  allocations: AllocationItem[];
  sector_diversification: Record<string, number>;
}

interface MarketTickerData {
  price: number;
  change: number;
  change_pct: number;
}

// Color map for sectors
const SECTOR_COLORS: Record<string, string> = {
  "Technology": "hsl(250, 85%, 65%)",       // Purple Indigo
  "Consumer Cyclical": "hsl(280, 80%, 65%)", // Magenta
  "Healthcare": "hsl(145, 80%, 45%)",        // Emerald Green
  "Financial Services": "hsl(190, 90%, 55%)", // Cyan Accent
};
const DEFAULT_COLOR = "hsl(35, 90%, 55%)"; // Orange Amber

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";


export default function Dashboard() {
  const [amount, setAmount] = useState<number>(50);
  const [riskLevel, setRiskLevel] = useState<string>("moderate");
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [marketData, setMarketData] = useState<Record<string, MarketTickerData>>({});
  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});
  const [flashStates, setFlashStates] = useState<Record<string, "up" | "down" | "">>({});
  const [expandedTicker, setExpandedTicker] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeploying, setIsDeploying] = useState<boolean>(false);
  const [deployedSuccess, setDeployedSuccess] = useState<boolean>(false);

  const socketRef = useRef<WebSocket | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch allocation data from FastAPI backend
  const fetchAllocation = async (targetAmount: number, targetRisk: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/allocate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: targetAmount, risk_level: targetRisk }),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch portfolio allocation.");
      }
      const data = await response.json();
      setPortfolio(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError("Unable to connect to backend server. Make sure the FastAPI app is running.");
    }
  };

  // Debounced fetch when amount or risk profile changes
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      fetchAllocation(amount, riskLevel);
    }, 150);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [amount, riskLevel]);

  // Connect to live WebSocket stream for price updates
  useEffect(() => {
    const connectWS = () => {
      const wsUrl = WS_BASE_URL;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log("WebSocket connected.");
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "initial_data" || message.type === "price_update") {
            const dataUpdates: Record<string, MarketTickerData> = message.market_data;
            
            // Determine price change directions for visual flashes
            setMarketData((currentMarketData) => {
              const newFlashStates: Record<string, "up" | "down" | ""> = {};
              
              Object.keys(dataUpdates).forEach((ticker) => {
                const oldPrice = currentMarketData[ticker]?.price;
                const newPrice = dataUpdates[ticker]?.price;
                
                if (oldPrice !== undefined && newPrice !== undefined) {
                  if (newPrice > oldPrice) {
                    newFlashStates[ticker] = "up";
                  } else if (newPrice < oldPrice) {
                    newFlashStates[ticker] = "down";
                  }
                }
              });

              // Apply flashes and clear them after 1 second
              if (Object.keys(newFlashStates).length > 0) {
                setFlashStates((prev) => ({ ...prev, ...newFlashStates }));
                setTimeout(() => {
                  setFlashStates((prev) => {
                    const cleared = { ...prev };
                    Object.keys(newFlashStates).forEach((tk) => {
                      cleared[tk] = "";
                    });
                    return cleared;
                  });
                }, 1000);
              }

              return dataUpdates;
            });
          }
        } catch (e) {
          console.error("Error parsing WebSocket message: ", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log("WebSocket closed. Attempting reconnect...");
        // Reconnect after 3 seconds
        setTimeout(connectWS, 3000);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error: ", err);
        ws.close();
      };

      socketRef.current = ws;
    };

    connectWS();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  // Update allocation elements if prices shift on websocket ticks
  useEffect(() => {
    if (!portfolio || Object.keys(marketData).length === 0) return;

    // Check if live prices changed, if so recalculate allocation values client-side
    let changed = false;
    const updatedAllocations = portfolio.allocations.map((item) => {
      const livePriceInfo = marketData[item.ticker];
      if (livePriceInfo && livePriceInfo.price !== item.price) {
        changed = true;
        // Keep the dollar allocation fixed, recalculate shares based on new live price
        return {
          ...item,
          price: livePriceInfo.price,
          shares: round(item.dollar_split / livePriceInfo.price, 6)
        };
      }
      return item;
    });

    if (changed) {
      setPortfolio((prev) => prev ? { ...prev, allocations: updatedAllocations } : null);
    }
  }, [marketData]);

  const round = (val: number, decimals: number) => {
    const factor = Math.pow(10, decimals);
    return Math.round(val * factor) / factor;
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setAmount(val);
    } else {
      setAmount(0);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAmount(parseInt(e.target.value, 10));
  };

  const executeInvestment = async () => {
    if (!portfolio || portfolio.allocations.length === 0) return;
    setIsDeploying(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/invest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          allocations: portfolio.allocations.map((a) => ({
            ticker: a.ticker,
            price: a.price,
            dollar_split: a.dollar_split,
            shares: a.shares
          }))
        })
      });
      
      if (!response.ok) {
        throw new Error("Failed to execute investment.");
      }
      
      const data = await response.json();
      console.log("Order execution response:", data);
      
      setIsDeploying(false);
      setDeployedSuccess(true);
      setTimeout(() => setDeployedSuccess(false), 5000);
    } catch (err: any) {
      console.error(err);
      setError("Failed to execute paper trade with brokerage API.");
      setIsDeploying(false);
    }
  };


  // Generate dynamic SVG Donut elements for sector breakdown
  const donutSlices = useMemo(() => {
    if (!portfolio) return [];
    
    const div = portfolio.sector_diversification || {};
    const entries = Object.entries(div).filter(([_, val]) => val > 0);
    
    let currentAngle = -90; // start at top (12 o'clock)
    const radius = 55;
    const cx = 80;
    const cy = 80;
    const circ = 2 * Math.PI * radius; // ~345.57

    return entries.map(([sector, pct]) => {
      const angle = (pct / 100) * 360;
      const strokeDashoffset = circ - (circ * pct) / 100;
      const rotation = currentAngle;
      
      currentAngle += angle;
      
      return {
        sector,
        pct,
        color: SECTOR_COLORS[sector] || DEFAULT_COLOR,
        rotation,
        strokeDasharray: circ,
        strokeDashoffset,
        radius,
        cx,
        cy
      };
    });
  }, [portfolio]);

  return (
    <div className="container">
      {/* Header Banner */}
      <header className="header">
        <div className="logo-section">
          <div className="logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <h1 className="logo-text">Aura<strong>Wealth</strong></h1>
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {isConnected ? (
            <div className="market-status">
              <span className="pulse-dot" style={{
                width: "8px", 
                height: "8px", 
                backgroundColor: "var(--color-success)", 
                borderRadius: "50%",
                display: "inline-block",
                boxShadow: "0 0 10px var(--color-success)"
              }}></span>
              Live Feed Connected
            </div>
          ) : (
            <div className="market-status" style={{
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              color: "var(--color-danger)",
              border: "1px solid rgba(239, 68, 68, 0.2)"
            }}>
              Connecting Live Stream...
            </div>
          )}
        </div>
      </header>

      {error && (
        <div style={{
          background: "rgba(239, 68, 68, 0.15)",
          border: "1px solid var(--color-danger)",
          borderRadius: "12px",
          padding: "1rem",
          color: "var(--color-danger)",
          marginBottom: "2rem"
        }}>
          <strong>Connection Error:</strong> {error}
        </div>
      )}

      {/* Main Grid Layout */}
      <div className="grid-layout">
        
        {/* Left Panel: Control and Inputs */}
        <section className="glass-card" style={{ height: "fit-content" }}>
          <div className="card-header-flex">
            <h2 className="card-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v8M8 12h8" />
              </svg>
              Micro-Allocator
            </h2>
          </div>

          <div className="input-group">
            <label className="input-label">Amount to Invest Today</label>
            <div className="amount-input-wrapper">
              <span className="amount-currency">$</span>
              <input
                type="number"
                className="amount-input"
                value={amount === 0 ? "" : amount}
                onChange={handleAmountChange}
                min="5"
                max="5000"
              />
            </div>
            <input
              type="range"
              className="range-slider"
              min="10"
              max="1000"
              step="5"
              value={amount}
              onChange={handleSliderChange}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "var(--text-muted)" }}>
              <span>Min: $10</span>
              <span>Max: $1000</span>
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Risk Profile Optimizer</label>
            <div className="risk-selector">
              {["conservative", "moderate", "aggressive"].map((level) => (
                <button
                  key={level}
                  className={`risk-button ${riskLevel === level ? "active" : ""}`}
                  onClick={() => setRiskLevel(level)}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <button 
            className="cta-button" 
            onClick={executeInvestment}
            disabled={isDeploying || !portfolio}
          >
            {isDeploying ? "Deploying Capital..." : "Deploy Portfolio"}
          </button>

          {deployedSuccess && (
            <div style={{
              marginTop: "1.5rem",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid var(--color-success)",
              borderRadius: "12px",
              padding: "1rem",
              textAlign: "center",
              color: "var(--color-success)"
            }}>
              🎉 <strong>Portfolio Deployed Successfully!</strong>
              <div style={{ fontSize: "0.85rem", marginTop: "0.25rem", color: "var(--text-secondary)" }}>
                Allocations placed in virtual paper account via Alpaca.
              </div>
            </div>
          )}

          {/* Sector Diversification Overview inside Left panel */}
          {portfolio && (
            <div style={{ marginTop: "2rem", borderTop: "1px solid var(--border-card)", paddingTop: "1.5rem" }}>
              <h3 className="card-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
                Sector Breakup
              </h3>
              
              <div className="donut-chart-container">
                <svg width="160" height="160" viewBox="0 0 160 160">
                  <circle cx="80" cy="80" r="55" fill="transparent" stroke="var(--bg-secondary)" strokeWidth="12" />
                  {donutSlices.map((slice, i) => (
                    <circle
                      key={i}
                      cx={slice.cx}
                      cy={slice.cy}
                      r={slice.radius}
                      fill="transparent"
                      stroke={slice.color}
                      strokeWidth="12"
                      strokeDasharray={slice.strokeDasharray}
                      strokeDashoffset={slice.strokeDashoffset}
                      transform={`rotate(${slice.rotation} 80 80)`}
                      strokeLinecap="round"
                    />
                  ))}
                  <text x="80" y="85" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="700" fontFamily="var(--font-display)">
                    {portfolio.allocations.length} Assets
                  </text>
                </svg>
              </div>

              <div className="sector-list">
                {Object.entries(portfolio.sector_diversification || {}).map(([sector, pct]) => (
                  <div key={sector} className="sector-card">
                    <div style={{ 
                      width: "10px", 
                      height: "10px", 
                      backgroundColor: SECTOR_COLORS[sector] || DEFAULT_COLOR, 
                      borderRadius: "50%",
                      margin: "0 auto 0.4rem"
                    }}></div>
                    <div className="sector-title">{sector}</div>
                    <div className="sector-value">{pct}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Right Panel: Recommendations & Fractions Calculations */}
        <section className="glass-card">
          <div className="card-header-flex">
            <h2 className="card-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2.5">
                <path d="M12 20V10M18 20V4M6 20v-4" />
              </svg>
              Research-Backed Picks
            </h2>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              Updated: Live Ticks (1.5s)
            </span>
          </div>

          {portfolio ? (
            <div className="table-container">
              <table className="alloc-table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th style={{ textAlign: "right" }}>Live Price</th>
                    <th style={{ textAlign: "right" }}>Weight</th>
                    <th style={{ textAlign: "right" }}>Split</th>
                    <th style={{ textAlign: "right" }}>Shares</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.allocations.map((stock) => {
                    const priceFlashClass = flashStates[stock.ticker] === "up" 
                      ? "flash-up" 
                      : flashStates[stock.ticker] === "down" 
                        ? "flash-down" 
                        : "";
                        
                    const mData = marketData[stock.ticker];
                    const changeVal = mData ? mData.change : 0;
                    const changePct = mData ? mData.change_pct : 0;

                    return (
                      <React.Fragment key={stock.ticker}>
                        <tr>
                          <td>
                            <span className="ticker-badge">{stock.ticker}</span>
                            <span className="stock-name">{stock.name}</span>
                          </td>
                          <td style={{ textAlign: "right" }} className={`price-text ${priceFlashClass}`}>
                            ${stock.price.toFixed(2)}
                            {changePct !== 0 && (
                              <div style={{
                                fontSize: "0.75rem",
                                color: changeVal >= 0 ? "var(--color-success)" : "var(--color-danger)",
                                marginTop: "0.15rem"
                              }}>
                                {changeVal >= 0 ? "+" : ""}{changePct.toFixed(2)}%
                              </div>
                            )}
                          </td>
                          <td style={{ textAlign: "right" }}>
                            <span className="weight-badge">{stock.allocation_pct}%</span>
                          </td>
                          <td style={{ textAlign: "right", fontWeight: "600" }}>
                            ${stock.dollar_split.toFixed(2)}
                          </td>
                          <td style={{ textAlign: "right", fontFamily: "monospace", color: "var(--text-secondary)", fontSize: "0.88rem" }}>
                            {stock.shares.toFixed(5)}
                          </td>
                          <td>
                            <button
                              className="why-badge-button"
                              onClick={() => setExpandedTicker(
                                expandedTicker === stock.ticker ? null : stock.ticker
                              )}
                            >
                              {expandedTicker === stock.ticker ? "Close" : "Research"}
                            </button>
                          </td>
                        </tr>
                        {/* Expandable AI explanation row */}
                        {expandedTicker === stock.ticker && (
                          <tr>
                            <td colSpan={6} style={{ padding: "0 1rem 1rem", borderBottom: "1px solid var(--border-card)" }}>
                              <div className="ai-why-card">
                                <div className="ai-why-title">
                                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                                    <line x1="12" y1="22.08" x2="12" y2="12" />
                                  </svg>
                                  AI Catalyst Summary (Real-Time Ingestion)
                                </div>
                                {stock.why_buy_today}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "4rem 0", color: "var(--text-muted)" }}>
              <div className="pulse-loader" style={{
                width: "40px",
                height: "40px",
                border: "3px solid var(--border-card)",
                borderTopColor: "var(--color-primary)",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
                margin: "0 auto 1rem"
              }}></div>
              Generating dynamic stock portfolio allocations...
              <style jsx>{`
                @keyframes spin {
                  to { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          )}
        </section>
      </div>

      <footer className="footer">
        <p>© 2026 AuraWealth Financial Technology. All recommendations are simulation outputs. Brokerage services provided by Alpaca API Paper sandbox.</p>
      </footer>
    </div>
  );
}
