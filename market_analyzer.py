import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from clob_client import ClobClient, Market, Token

logger = logging.getLogger('polymarket_bot')

@dataclass
class PricePoint:
    """Single price data point"""
    timestamp: datetime
    price: float
    probability: float

@dataclass
class MarketSignal:
    """Trading signal for a market"""
    market_id: str
    direction: str  # 'up', 'down', 'neutral'
    confidence: float  # 0.0 to 1.0
    probability: float  # market probability
    timestamp: datetime
    price_history: List[PricePoint]

class MarketAnalyzer:
    """Analyzes market data to determine trading direction"""
    
    def __init__(self, client: ClobClient):
        self.client = client
        self.price_history: Dict[str, List[PricePoint]] = {}
        self.watch_duration = 300  # 5 minutes in seconds
        
    async def start_watching_market(self, market: Market) -> MarketSignal:
        """Watch a market for 5 minutes and determine direction"""
        logger.info(f"Starting to watch market: {market.question}")
        
        # Initialize price history
        self.price_history[market.id] = []
        start_time = datetime.now()
        
        # Collect price data for 5 minutes
        while (datetime.now() - start_time).total_seconds() < self.watch_duration:
            try:
                tokens = await self.client.get_market_prices(market.id)
                
                # Find up and down tokens
                up_token = None
                down_token = None
                
                for token in tokens:
                    outcome_lower = token.outcome.lower()
                    if 'up' in outcome_lower:
                        up_token = token
                    elif 'down' in outcome_lower:
                        down_token = token
                
                if up_token and down_token:
                    timestamp = datetime.now()
                    
                    # Record price points
                    self.price_history[market.id].append(
                        PricePoint(timestamp, up_token.price, up_token.probability)
                    )
                    self.price_history[market.id].append(
                        PricePoint(timestamp, down_token.price, down_token.probability)
                    )
                    
                    logger.debug(f"Recorded prices - Up: {up_token.price:.4f} ({up_token.probability:.2%}), "
                               f"Down: {down_token.price:.4f} ({down_token.probability:.2%})")
                
                # Wait before next reading
                await asyncio.sleep(10)  # Read every 10 seconds
                
            except Exception as e:
                logger.error(f"Error watching market {market.id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        # Analyze the collected data
        signal = await self._analyze_price_history(market)
        logger.info(f"Analysis complete for {market.question}: {signal.direction} "
                   f"(confidence: {signal.confidence:.2%}, probability: {signal.probability:.2%})")
        
        return signal
    
    async def _analyze_price_history(self, market: Market) -> MarketSignal:
        """Analyze price history to determine direction and confidence"""
        market_id = market.id
        history = self.price_history.get(market_id, [])
        
        if len(history) < 6:  # Need at least some data points
            return MarketSignal(
                market_id=market_id,
                direction='neutral',
                confidence=0.0,
                probability=0.5,
                timestamp=datetime.now(),
                price_history=history
            )
        
        # Separate up and down price points
        up_prices = []
        down_prices = []
        
        for i, point in enumerate(history):
            if i % 2 == 0:  # Assuming up token comes first
                up_prices.append(point.price)
            else:
                down_prices.append(point.price)
        
        # Calculate trends
        up_trend = self._calculate_trend(up_prices)
        down_trend = self._calculate_trend(down_prices)
        
        # Determine direction based on trends
        direction = 'neutral'
        confidence = 0.0
        
        if abs(up_trend) > 0.001 or abs(down_trend) > 0.001:  # Minimum threshold
            if up_trend > down_trend and up_trend > 0:
                direction = 'up'
                confidence = min(abs(up_trend) * 100, 1.0)
            elif down_trend > up_trend and down_trend > 0:
                direction = 'down'
                confidence = min(abs(down_trend) * 100, 1.0)
        
        # Get current probability
        current_probability = 0.5
        if history:
            current_probability = history[-1].probability
        
        return MarketSignal(
            market_id=market_id,
            direction=direction,
            confidence=confidence,
            probability=current_probability,
            timestamp=datetime.now(),
            price_history=history
        )
    
    def _calculate_trend(self, prices: List[float]) -> float:
        """Calculate trend using linear regression"""
        if len(prices) < 2:
            return 0.0
        
        x = np.arange(len(prices))
        y = np.array(prices)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
        
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) if len(returns) > 0 else 0.0
    
    def _calculate_momentum(self, prices: List[float], period: int = 5) -> float:
        """Calculate price momentum"""
        if len(prices) < period + 1:
            return 0.0
        
        current_price = prices[-1]
        past_price = prices[-(period + 1)]
        
        return (current_price - past_price) / past_price if past_price > 0 else 0.0
    
    async def get_best_btc_market(self) -> Optional[Market]:
        """Find the best BTC 15m market to trade"""
        try:
            btc_markets = await self.client.get_btc_15m_markets()
            
            if not btc_markets:
                logger.warning("No active 15m BTC markets found")
                return None
            
            # Score markets based on liquidity and volume
            best_market = None
            best_score = 0
            
            for market in btc_markets:
                score = market.liquidity + (market.volume * 0.1)
                if score > best_score:
                    best_score = score
                    best_market = market
            
            logger.info(f"Selected best BTC market: {best_market.question} (score: {best_score:.2f})")
            return best_market
            
        except Exception as e:
            logger.error(f"Failed to find best BTC market: {e}")
            return None
