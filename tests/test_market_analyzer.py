import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_analyzer import MarketAnalyzer, PricePoint, MarketSignal
from polymarket_client import PolymarketClient, Market, Token

@pytest.fixture
def mock_client():
    """Mock PolymarketClient"""
    client = AsyncMock(spec=PolymarketClient)
    return client

@pytest.fixture
def mock_btc_market():
    """Mock BTC market"""
    return Market(
        id='btc_market_1',
        question='Will BTC go up in the next 15 minutes?',
        description='BTC 15-minute price prediction',
        end_date='2024-12-31T23:59:59Z',
        active=True,
        volume=1000.0,
        liquidity=500.0,
        tokens=[],
        created_at='2024-01-01T00:00:00Z',
        slug='btc-15m-up'
    )

@pytest.fixture
def mock_tokens():
    """Mock market tokens"""
    return [
        Token(
            id='token_up',
            outcome='Up',
            price=0.65,
            probability=0.65,
            supply=1000.0
        ),
        Token(
            id='token_down',
            outcome='Down',
            price=0.35,
            probability=0.35,
            supply=800.0
        )
    ]

@pytest.fixture
def analyzer(mock_client):
    """Create MarketAnalyzer instance"""
    return MarketAnalyzer(mock_client)

class TestMarketAnalyzer:
    """Test cases for MarketAnalyzer"""
    
    def test_analyzer_initialization(self, mock_client):
        """Test analyzer initialization"""
        analyzer = MarketAnalyzer(mock_client)
        assert analyzer.client == mock_client
        assert analyzer.price_history == {}
        assert analyzer.watch_duration == 300
    
    def test_calculate_trend(self, analyzer):
        """Test trend calculation"""
        # Test upward trend
        prices_up = [0.5, 0.55, 0.6, 0.65, 0.7]
        trend = analyzer._calculate_trend(prices_up)
        assert trend > 0
        
        # Test downward trend
        prices_down = [0.7, 0.65, 0.6, 0.55, 0.5]
        trend = analyzer._calculate_trend(prices_down)
        assert trend < 0
        
        # Test flat trend
        prices_flat = [0.6, 0.6, 0.6, 0.6, 0.6]
        trend = analyzer._calculate_trend(prices_flat)
        assert abs(trend) < 0.001
        
        # Test insufficient data
        trend = analyzer._calculate_trend([0.5])
        assert trend == 0.0
    
    def test_calculate_volatility(self, analyzer):
        """Test volatility calculation"""
        # Test with varying prices
        prices = [0.5, 0.6, 0.4, 0.7, 0.3]
        volatility = analyzer._calculate_volatility(prices)
        assert volatility > 0
        
        # Test with stable prices
        stable_prices = [0.5, 0.5, 0.5, 0.5, 0.5]
        volatility = analyzer._calculate_volatility(stable_prices)
        assert volatility == 0.0
        
        # Test insufficient data
        volatility = analyzer._calculate_volatility([0.5])
        assert volatility == 0.0
    
    def test_calculate_momentum(self, analyzer):
        """Test momentum calculation"""
        prices = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75]
        momentum = analyzer._calculate_momentum(prices, period=3)
        
        # Should be positive (upward momentum)
        assert momentum > 0
        
        # Test with insufficient data
        momentum = analyzer._calculate_momentum([0.5, 0.6], period=5)
        assert momentum == 0.0
    
    @pytest.mark.asyncio
    async def test_start_watching_market(self, analyzer, mock_btc_market, mock_tokens):
        """Test market watching functionality"""
        # Mock the client methods
        analyzer.client.get_market_prices = AsyncMock(return_value=mock_tokens)
        
        # Mock time to avoid waiting 5 minutes in tests
        with patch('asyncio.sleep', return_value=None):
            # Mock the watch duration to be very short for testing
            analyzer.watch_duration = 1
            
            signal = await analyzer.start_watching_market(mock_btc_market)
            
            assert signal.market_id == mock_btc_market.id
            assert signal.direction in ['up', 'down', 'neutral']
            assert 0 <= signal.confidence <= 1.0
            assert isinstance(signal.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_analyze_price_history(self, analyzer, mock_btc_market):
        """Test price history analysis"""
        # Create mock price history
        now = datetime.now()
        price_history = [
            PricePoint(now, 0.5, 0.5),
            PricePoint(now, 0.6, 0.6),
            PricePoint(now, 0.7, 0.7),
            PricePoint(now, 0.8, 0.8),
        ]
        
        analyzer.price_history[mock_btc_market.id] = price_history
        
        signal = await analyzer._analyze_price_history(mock_btc_market)
        
        assert signal.market_id == mock_btc_market.id
        assert signal.direction in ['up', 'down', 'neutral']
        assert 0 <= signal.confidence <= 1.0
        assert signal.price_history == price_history
    
    @pytest.mark.asyncio
    async def test_analyze_price_history_insufficient_data(self, analyzer, mock_btc_market):
        """Test analysis with insufficient data"""
        # Create minimal price history
        price_history = [
            PricePoint(datetime.now(), 0.5, 0.5),
        ]
        
        analyzer.price_history[mock_btc_market.id] = price_history
        
        signal = await analyzer._analyze_price_history(mock_btc_market)
        
        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_get_best_btc_market(self, analyzer):
        """Test finding best BTC market"""
        # Mock markets
        btc_markets = [
            Market(
                id='market1',
                question='Will BTC go up in the next 15 minutes?',
                description='BTC prediction',
                end_date='2024-12-31T23:59:59Z',
                active=True,
                volume=1000.0,
                liquidity=500.0,
                tokens=[],
                created_at='2024-01-01T00:00:00Z',
                slug='btc-15m-1'
            ),
            Market(
                id='market2',
                question='Will BTC go down in the next 15 minutes?',
                description='BTC prediction',
                end_date='2024-12-31T23:59:59Z',
                active=True,
                volume=2000.0,
                liquidity=800.0,
                tokens=[],
                created_at='2024-01-01T00:00:00Z',
                slug='btc-15m-2'
            ),
            Market(
                id='market3',
                question='Will ETH go up in the next 15 minutes?',
                description='ETH prediction',
                end_date='2024-12-31T23:59:59Z',
                active=True,
                volume=1500.0,
                liquidity=600.0,
                tokens=[],
                created_at='2024-01-01T00:00:00Z',
                slug='eth-15m-1'
            )
        ]
        
        analyzer.client.get_btc_15m_markets = AsyncMock(return_value=btc_markets)
        
        best_market = await analyzer.get_best_btc_market()
        
        # Should return the BTC market with highest score (market2 due to higher volume and liquidity)
        assert best_market.id == 'market2'
        assert 'btc' in best_market.question.lower()
    
    @pytest.mark.asyncio
    async def test_get_best_btc_market_no_markets(self, analyzer):
        """Test when no BTC markets are available"""
        analyzer.client.get_btc_15m_markets = AsyncMock(return_value=[])
        
        best_market = await analyzer.get_best_btc_market()
        
        assert best_market is None
    
    @pytest.mark.asyncio
    async def test_market_signal_creation(self):
        """Test MarketSignal dataclass"""
        timestamp = datetime.now()
        signal = MarketSignal(
            market_id='test_market',
            direction='up',
            confidence=0.8,
            probability=0.75,
            timestamp=timestamp,
            price_history=[]
        )
        
        assert signal.market_id == 'test_market'
        assert signal.direction == 'up'
        assert signal.confidence == 0.8
        assert signal.probability == 0.75
        assert signal.timestamp == timestamp
        assert signal.price_history == []
    
    def test_price_point_creation(self):
        """Test PricePoint dataclass"""
        timestamp = datetime.now()
        price_point = PricePoint(
            timestamp=timestamp,
            price=0.65,
            probability=0.65
        )
        
        assert price_point.timestamp == timestamp
        assert price_point.price == 0.65
        assert price_point.probability == 0.65

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
