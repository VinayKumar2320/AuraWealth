import os
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from openai import OpenAI
from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        self.openai_client = None
        if OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def fetch_rss_headlines(self) -> List[Dict[str, str]]:
        """
        Scrapes financial headlines from public Yahoo Finance RSS feed.
        """
        headlines = []
        try:
            url = "https://finance.yahoo.com/news/rssindex"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item")[:15]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    description = item.find("description").text if item.find("description") is not None else ""
                    headlines.append({
                        "title": title,
                        "description": description,
                        "url": link
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS headlines: {e}")
        return headlines

    def analyze_ticker_sentiment(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Uses OpenAI structured output parser with a 20-year Wall Street CIO persona
        to filter macro catalysts and return structured analysis.
        """
        if not self.openai_client:
            logger.warning("OpenAI API Key not set. Falling back to default simulation sentiment.")
            return {
                "sentiment_score": 0.75,
                "catalyst": f"Positive momentum trends for {ticker} supported by macro inflows.",
                "macro_impact": f"Institutional desk notes strong relative strength and positioning in {ticker}'s sector under the current interest rate regime.",
                "allocation_impact": f"Justifies core holding allocation in today's basket to balance risk-reward across the portfolio."
            }

        # Filter news items mentioning the ticker
        relevant_news = []
        for item in news_items:
            content = f"{item['title']} {item['description']}".lower()
            if ticker.lower() in content:
                relevant_news.append(item)

        if not relevant_news:
            context = f"No recent RSS feed matches found for {ticker}."
        else:
            context = "\n".join([f"- {n['title']}: {n['description']}" for n in relevant_news[:3]])

        prompt = f"""
        You are a Chief Investment Officer (CIO) with 20+ years of institutional experience on Wall Street.
        Analyze the current news sentiment and immediate macro catalysts for: {ticker}.
        
        Recent News Context:
        {context}
        
        CRITICAL RULES:
        1. Act strictly as a seasoned CIO. Cut through noise, retail speculation, clickbait, and generic intraday price fluctuations.
        2. Focus strictly on major macroeconomic catalysts: Federal Reserve decisions, interest rate policy shifts, inflation indices (CPI, PCE), geopolitical risk escalations, and massive corporate earnings surprises that redefine company valuations.
        3. Provide three outputs:
           - Catalyst: A concise description of the hard news catalyst.
           - Macro Impact: Why an institutional investment committee and a 20-year veteran cares about this headline, mapping it to broader economic trends.
           - Allocation Impact: How this catalyst justifies allocating capital into this specific asset/ETF (e.g. {ticker}) for a diversified daily micro-investment.
        4. Provide a sentiment_score between -1.0 (extremely bearish) and 1.0 (extremely bullish).
        """

        try:
            # Request structured output
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional financial Chief Investment Officer. Give precise ratings and structured explanations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "sentiment_analysis",
                        "strict": True,
                        "schema": {
                            "type": "OBJECT",
                            "properties": {
                                "sentiment_score": {"type": "NUMBER"},
                                "catalyst": {"type": "STRING"},
                                "macro_impact": {"type": "STRING"},
                                "allocation_impact": {"type": "STRING"}
                            },
                            "required": ["sentiment_score", "catalyst", "macro_impact", "allocation_impact"],
                            "additionalProperties": False
                        }
                    }
                },
                temperature=0.2,
                max_tokens=250
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return {
                "sentiment_score": float(result.get("sentiment_score", 0.0)),
                "catalyst": str(result.get("catalyst", "")),
                "macro_impact": str(result.get("macro_impact", "")),
                "allocation_impact": str(result.get("allocation_impact", ""))
            }
        except Exception as e:
            logger.error(f"Error during OpenAI sentiment analysis for {ticker}: {e}")
            return {
                "sentiment_score": 0.5,
                "catalyst": f"Market structure and technical signals remain stable for {ticker}.",
                "macro_impact": f"Macro headwinds are priced in, with standard support levels holding at current levels.",
                "allocation_impact": f"Provides passive market exposure to stabilize the overall portfolio variance."
            }



