import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymarket_client import PolymarketClient, Market, Token

@pytest.fixture
def mock_market_data():
    """Mock market data for testing"""
    return [
        {
            'id': 'market1',
            'question': 'Will BTC go up in the next 15 minutes?',
            'description': 'BTC price prediction',
            'endDate': '2024-01-01T00:00:00Z',
            'active': True,
            'volume': 1000.0,
            'liquidity': 500.0,
            'tokens': [
                {'id': 'token1', 'outcome': 'Up', 'price': 0.6, 'probability': 0.6, 'supply': 1000},
                {'id': 'token2', 'outcome': 'Down', 'price': 0.4, 'probability': 0.4, 'supply': 800}
            ],
            'createdAt': '2024-01-01T00:00:00Z',
            'slug': 'btc-15m-up'
        },
        {
            'id': 'market2',
            'question': 'Will BTC go down in the next 15 minutes?',
            'description': 'BTC price prediction',
            'endDate': '2024-01-01T00:00:00Z',
            'active': True,
            'volume': 800.0,
            'liquidity': 400.0,
            'tokens': [
                {'id': 'token3', 'outcome': 'Up', 'price': 0.5, 'probability': 0.5, 'supply': 900},
                {'id': 'token4', 'outcome': 'Down', 'price': 0.5, 'probability': 0.5, 'supply': 700}
            ],
            'createdAt': '2024-01-01T00:00:00Z',
            'slug': 'btc-15m-down'
        }
    ]

@pytest.fixture
async def client():
    """Create a test client"""
    client = PolymarketClient()
    yield client
    if client.session:
        await client.session.close()

class TestPolymarketClient:
    """Test cases for PolymarketClient"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization"""
        client = PolymarketClient()
        assert client.base_url is not None
        assert client.graphql_url is not None
        assert client.session is None
        await client.__aexit__(None, None, None)
    
    @pytest.mark.asyncio
    async def test_session_creation(self, client):
        """Test session creation"""
        async with client:
            assert client.session is not None
            assert not client.session.closed
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_active_markets_success(self, mock_get, client, mock_market_data):
        """Test successful fetching of active markets"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_market_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with client:
            markets = await client.get_active_markets()
            
            assert len(markets) == 2
            assert markets[0].id == 'market1'
            assert markets[0].active is True
            assert markets[0].question == 'Will BTC go up in the next 15 minutes?'
            assert len(markets[0].tokens) == 2
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_active_markets_http_error(self, mock_get, client):
        """Test handling of HTTP errors"""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with client:
            with pytest.raises(Exception):
                await client.get_active_markets()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_btc_15m_markets(self, mock_get, client, mock_market_data):
        """Test filtering of BTC 15m markets"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_market_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with client:
            btc_markets = await client.get_btc_15m_markets()
            
            assert len(btc_markets) == 2
            for market in btc_markets:
                assert 'btc' in market.question.lower()
                assert '15m' in market.question.lower() or '15 min' in market.question.lower()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_market_prices(self, mock_get, client):
        """Test fetching market prices"""
        token_data = [
            {'id': 'token1', 'outcome': 'Up', 'price': 0.6, 'probability': 0.6, 'supply': 1000},
            {'id': 'token2', 'outcome': 'Down', 'price': 0.4, 'probability': 0.4, 'supply': 800}
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with client:
            tokens = await client.get_market_prices('market1')
            
            assert len(tokens) == 2
            assert tokens[0].outcome == 'Up'
            assert tokens[0].price == 0.6
            assert tokens[0].probability == 0.6
            assert tokens[1].outcome == 'Down'
            assert tokens[1].price == 0.4
            assert tokens[1].probability == 0.4
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check"""
        with patch.object(client, '_ensure_session') as mock_ensure:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            mock_ensure.return_value = None
            client.session = mock_session
            
            result = await client.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check failure"""
        with patch.object(client, '_ensure_session') as mock_ensure:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            mock_ensure.return_value = None
            client.session = mock_session
            
            result = await client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_self_healing_session_recreation(self, client):
        """Test self-healing session recreation"""
        # First session creation
        await client._ensure_session()
        first_session = client.session
        
        # Simulate session closure
        await first_session.close()
        
        # Should create new session
        await client._ensure_session()
        second_session = client.session
        
        assert first_session != second_session
        assert not first_session.closed or second_session != first_session
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_retry_mechanism(self, mock_get, client):
        """Test retry mechanism for failed requests"""
        # Mock failed responses followed by success
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json = AsyncMock(return_value=[])
        
        # First two calls fail, third succeeds
        mock_get.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        async with client:
            # Should eventually succeed after retries
            result = await client.get_active_markets()
            assert result == []
            assert mock_get.call_count == 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
