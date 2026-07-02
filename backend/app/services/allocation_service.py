from typing import List, Dict, Any

class AllocationService:
    @staticmethod
    def calculate_allocation(amount: float, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a total dollar amount and a list of stocks.
        Returns the exact dollar split and fractional share counts, plus diversification mixes.
        """
        if amount <= 0 or not stocks:
            return {
                "total_allocated": 0.0,
                "allocations": [],
                "sector_diversification": {},
                "asset_class_diversification": {}
            }

        # Normalize raw scores to ensure they are all positive for weighting
        min_score = min(s["raw_score"] for s in stocks)
        adjusted_scores = []
        for s in stocks:
            adj_score = s["raw_score"] + abs(min_score) + 1.0
            adjusted_scores.append(adj_score)
            
        total_score = sum(adjusted_scores)
        
        # Calculate raw allocations
        allocations = []
        allocated_sum = 0.0
        
        for i, stock in enumerate(stocks):
            weight = adjusted_scores[i] / total_score
            dollar_split = round(amount * weight, 2)
            allocated_sum += dollar_split
            
            allocations.append({
                "ticker": stock["ticker"],
                "name": stock["name"],
                "sector": stock["sector"],
                "asset_class": stock.get("asset_class", "Equities"),
                "price": stock["price"],
                "sentiment_score": stock["sentiment_score"],
                "catalyst": stock.get("catalyst", ""),
                "macro_impact": stock.get("macro_impact", ""),
                "allocation_impact": stock.get("allocation_impact", ""),
                "allocation_pct": round(weight * 100, 2),
                "dollar_split": dollar_split,
                "shares": 0.0 # Will calculate after adjustment
            })
            
        # Adjust rounding errors so the sum of dollar splits is EXACTLY the input amount
        difference = round(amount - allocated_sum, 2)
        if difference != 0 and len(allocations) > 0:
            max_alloc = max(allocations, key=lambda x: x["dollar_split"])
            max_alloc["dollar_split"] = round(max_alloc["dollar_split"] + difference, 2)
            
        # Recalculate percentage weights based on final dollar splits and compute shares
        final_sum = sum(a["dollar_split"] for a in allocations)
        for a in allocations:
            a["allocation_pct"] = round((a["dollar_split"] / final_sum) * 100, 2) if final_sum > 0 else 0.0
            a["shares"] = round(a["dollar_split"] / a["price"], 6) if a["price"] > 0 else 0.0
            
        # Group by sector to calculate diversification mix
        sector_mix = {}
        for a in allocations:
            sector = a["sector"]
            sector_mix[sector] = round(sector_mix.get(sector, 0.0) + a["allocation_pct"], 2)

        # Group by asset class to calculate diversification mix
        asset_class_mix = {}
        for a in allocations:
            ac = a["asset_class"]
            asset_class_mix[ac] = round(asset_class_mix.get(ac, 0.0) + a["allocation_pct"], 2)

        return {
            "total_allocated": round(final_sum, 2),
            "allocations": allocations,
            "sector_diversification": sector_mix,
            "asset_class_diversification": asset_class_mix
        }


