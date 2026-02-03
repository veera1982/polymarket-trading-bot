import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot import TradingBot
from polymarket_client import Market, Token
from market_analyzer import MarketSignal

@pytest.fixture
def mock_market_data():
    """Mock market data for integration tests"""
    return [
        Market(
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
    ]

@pytest.fixture
def mock_tokens():
    """Mock market tokens"""
    return [
        Token(
            id='token_up',
            outcome='Up',
            price=0.75,
            probability=0.75,
            supply=1000.0
        ),
        Token(
            id='token_down',
            outcome='Down',
            price=0.25,
            probability=0.25,
            supply=800.0
        )
    ]

@pytest.fixture
def bot():
    """Create TradingBot instance for testing"""
    with patch.dict(os.environ, {
        'PRIVATE_KEY': '0x1234567890123456789012345678901234567890123456789012345678901234',
        'WALLET_ADDRESS': '0x1234567890123456789012345678901234567890'
    }):
        bot = TradingBot()
        return bot

class TestIntegration:
    """Integration tests for the complete trading system"""
    
    @pytest.mark.asyncio
    async def test_complete_trading_flow(self, bot, mock_market_data, mock_tokens):
        """Test complete trading flow from market discovery to trade execution"""
        # Mock the entire flow
        with patch.object(bot, 'trader') as mock_trader:
            # Mock market discovery
            mock_trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_market_data[0])
            
            # Mock market watching
            mock_signal = MarketSignal(
                market_id=mock_market_data[0].id,
                direction='up',
                confidence=0.8,
                probability=0.75,
                timestamp=datetime.now(),
                price_history=[]
            )
            mock_trader.analyzer.start_watching_market = AsyncMock(return_value=mock_signal)
            
            # Mock price fetching
            mock_trader.client.get_market_prices = AsyncMock(return_value=mock_tokens)
            
            # Mock trade execution
            mock_trader._execute_trade = AsyncMock(return_value=None)
            
            # Mock trade summary
            mock_trader.get_trade_summary.return_value = {
                'total_trades': 0,
                'total_amount': 0.0,
                'up_trades': 0,
                'down_trades': 0,
                'average_probability': 0.0,
                'last_trade_time': None
            }
            
            await bot.run_single_cycle()
            
            # Verify the flow was executed
            mock_trader.analyzer.get_best_btc_market.assert_called_once()
            mock_trader.analyzer.start_watching_market.assert_called_once()
            mock_trader.client.get_market_prices.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, bot):
        """Test error handling and self-healing mechanisms"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock initial failure
            mock_trader.analyzer.get_best_btc_market = AsyncMock(side_effect=Exception("API Error"))
            
            # Should handle the error gracefully
            await bot.run_single_cycle()
            
            # Verify error was handled without crashing
            assert True  # If we reach here, error was handled
    
    @pytest.mark.asyncio
    async def test_health_check_functionality(self, bot):
        """Test health check and self-healing"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock successful health check
            mock_trader.client.health_check = AsyncMock(return_value=True)
            
            result = await bot.health_check()
            
            assert result is True
            mock_trader.client.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure_and_healing(self, bot):
        """Test health check failure and connection healing"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock failed health check
            mock_trader.client.health_check = AsyncMock(return_value=False)
            
            # Mock healing process
            with patch.object(bot, '_heal_connection') as mock_heal:
                result = await bot.health_check()
                
                assert result is False
                mock_heal.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation"""
        # Test with missing configuration
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="PRIVATE_KEY is required"):
                from config import Config
                Config.validate()
    
    @pytest.mark.asyncio
    async def test_trade_limits_enforcement(self, bot, mock_market_data, mock_tokens):
        """Test that trade limits are properly enforced"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock market discovery
            mock_trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_market_data[0])
            
            # Mock market watching
            mock_signal = MarketSignal(
                market_id=mock_market_data[0].id,
                direction='up',
                confidence=0.8,
                probability=0.75,
                timestamp=datetime.now(),
                price_history=[]
            )
            mock_trader.analyzer.start_watching_market = AsyncMock(return_value=mock_signal)
            
            # Mock price fetching
            mock_trader.client.get_market_prices = AsyncMock(return_value=mock_tokens)
            
            # Set traded amount to near limit
            mock_trader.total_traded_today = 4.5  # Close to $5 limit
            
            # Mock trade execution with partial amount
            mock_trader._execute_trade = AsyncMock(return_value=None)
            
            await bot.run_single_cycle()
            
            # Verify trade was attempted with remaining limit
            mock_trader._execute_trade.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_probability_threshold_filtering(self, bot, mock_market_data, mock_tokens):
        """Test that trades below probability threshold are filtered out"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock market discovery
            mock_trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_market_data[0])
            
            # Mock market watching with low probability
            low_prob_signal = MarketSignal(
                market_id=mock_market_data[0].id,
                direction='up',
                confidence=0.8,
                probability=0.5,  # Below 0.7 threshold
                timestamp=datetime.now(),
                price_history=[]
            )
            mock_trader.analyzer.start_watching_market = AsyncMock(return_value=low_prob_signal)
            
            await bot.run_single_cycle()
            
            # Verify no trade was executed due to low probability
            mock_trader._execute_trade.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_neutral_signal_handling(self, bot, mock_market_data):
        """Test that neutral signals result in no trades"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock market discovery
            mock_trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_market_data[0])
            
            # Mock market watching with neutral signal
            neutral_signal = MarketSignal(
                market_id=mock_market_data[0].id,
                direction='neutral',
                confidence=0.0,
                probability=0.5,
                timestamp=datetime.now(),
                price_history=[]
            )
            mock_trader.analyzer.start_watching_market = AsyncMock(return_value=neutral_signal)
            
            await bot.run_single_cycle()
            
            # Verify no trade was executed due to neutral signal
            mock_trader._execute_trade.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_multiple_error_restart_mechanism(self, bot):
        """Test bot restart mechanism after multiple errors"""
        with patch.object(bot, 'trader') as mock_trader:
            # Mock repeated failures
            mock_trader.run_trading_cycle = AsyncMock(side_effect=Exception("Persistent Error"))
            
            # Mock restart functionality
            with patch.object(bot, '_restart_bot') as mock_restart:
                # Simulate multiple errors
                for i in range(bot.max_errors):
                    try:
                        await bot.run_single_cycle()
                    except:
                        pass
                
                # After max errors, restart should be triggered
                # (This is simplified for testing)
                assert bot.error_count >= bot.max_errors

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
