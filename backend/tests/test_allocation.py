import unittest
from app.services.allocation_service import AllocationService

class TestAllocationService(unittest.TestCase):
    def setUp(self):
        self.stocks = [
            {"ticker": "AAPL", "name": "Apple", "sector": "Technology", "price": 200.0, "sentiment_score": 0.8, "why_buy_today": "Good pre-orders", "raw_score": 1.5},
            {"ticker": "MSFT", "name": "Microsoft", "sector": "Technology", "price": 400.0, "sentiment_score": 0.7, "why_buy_today": "Cloud growth", "raw_score": 1.2},
            {"ticker": "NVDA", "name": "Nvidia", "sector": "Technology", "price": 100.0, "sentiment_score": 0.9, "why_buy_today": "Blackwell sold out", "raw_score": 2.0},
            {"ticker": "TSLA", "name": "Tesla", "sector": "Consumer Cyclical", "price": 200.0, "sentiment_score": 0.5, "why_buy_today": "FSD approved", "raw_score": -0.5}, # negative score test
            {"ticker": "UNH", "name": "UnitedHealth", "sector": "Healthcare", "price": 500.0, "sentiment_score": 0.6, "why_buy_today": "Beat earnings", "raw_score": 0.8}
        ]

    def test_allocation_sum_is_exact(self):
        # Invest $50
        amount = 50.0
        result = AllocationService.calculate_allocation(amount, self.stocks)
        self.assertEqual(result["total_allocated"], amount)
        
        # Verify sum of splits is exactly equal to amount
        splits_sum = sum(a["dollar_split"] for a in result["allocations"])
        self.assertEqual(splits_sum, amount)
        
        # Verify sum of percentages is close to 100%
        pct_sum = sum(a["allocation_pct"] for a in result["allocations"])
        self.assertAlmostEqual(pct_sum, 100.0, places=1)

    def test_allocation_sum_large_amount(self):
        # Invest $999.99
        amount = 999.99
        result = AllocationService.calculate_allocation(amount, self.stocks)
        self.assertEqual(result["total_allocated"], amount)
        
        splits_sum = sum(a["dollar_split"] for a in result["allocations"])
        self.assertEqual(splits_sum, amount)

    def test_zero_amount(self):
        result = AllocationService.calculate_allocation(0, self.stocks)
        self.assertEqual(result["total_allocated"], 0.0)
        self.assertEqual(len(result["allocations"]), 0)

    def test_negative_amount(self):
        result = AllocationService.calculate_allocation(-50.0, self.stocks)
        self.assertEqual(result["total_allocated"], 0.0)
        self.assertEqual(len(result["allocations"]), 0)

if __name__ == "__main__":
    unittest.main()
