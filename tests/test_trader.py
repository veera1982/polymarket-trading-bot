import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trader import Trader, Trade
from polymarket_client import Market, Token
from market_analyzer import MarketSignal
from config import Config

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
def mock_market_signal():
    """Mock market signal"""
    return MarketSignal(
        market_id='btc_market_1',
        direction='up',
        confidence=0.8,
        probability=0.75,
        timestamp=datetime.now(),
        price_history=[]
    )

@pytest.fixture
def trader():
    """Create Trader instance"""
    with patch.dict(os.environ, {
        'PRIVATE_KEY': '0x1234567890123456789012345678901234567890123456789012345678901234',
        'WALLET_ADDRESS': '0x1234567890123456789012345678901234567890'
    }):
        trader = Trader()
        return trader

class TestTrader:
    """Test cases for Trader"""
    
    def test_trader_initialization(self):
        """Test trader initialization"""
        with patch.dict(os.environ, {
            'PRIVATE_KEY': '0x1234567890123456789012345678901234567890123456789012345678901234',
            'WALLET_ADDRESS': '0x1234567890123456789012345678901234567890'
        }):
            trader = Trader()
            assert trader.client is not None
            assert trader.analyzer is not None
            assert trader.total_traded_today == 0.0
            assert trader.trade_history == []
    
    def test_trade_creation(self):
        """Test Trade dataclass"""
        timestamp = datetime.now()
        trade = Trade(
            id='test_trade',
            market_id='test_market',
            direction='up',
            amount=0.8,
            price=0.75,
            probability=0.75,
            timestamp=timestamp
        )
        
        assert trade.id == 'test_trade'
        assert trade.market_id == 'test_market'
        assert trade.direction == 'up'
        assert trade.amount == 0.8
        assert trade.price == 0.75
        assert trade.probability == 0.75
        assert trade.timestamp == timestamp
        assert trade.status == 'pending'
        assert trade.tx_hash is None
    
    @pytest.mark.asyncio
    async def test_find_and_trade_btc_15m_success(self, trader, mock_btc_market, mock_market_signal):
        """Test successful BTC 15m trade finding and execution"""
        # Mock the analyzer methods
        trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_btc_market)
        trader.analyzer.start_watching_market = AsyncMock(return_value=mock_market_signal)
        
        # Mock client methods
        trader.client.get_market_prices = AsyncMock(return_value=[
            Token('token_up', 'Up', 0.75, 0.75, 1000),
            Token('token_down', 'Down', 0.25, 0.25, 800)
        ])
        
        # Mock trade execution
        with patch.object(trader, '_execute_trade') as mock_execute:
            mock_trade = Trade(
                id='test_trade',
                market_id=mock_btc_market.id,
                direction='up',
                amount=0.8,
                price=0.75,
                probability=0.75,
                timestamp=datetime.now(),
                status='confirmed'
            )
            mock_execute.return_value = mock_trade
            
            trade = await trader.find_and_trade_btc_15m()
            
            assert trade is not None
            assert trade.direction == 'up'
            assert trade.amount == 0.8
            assert trade.status == 'confirmed'
            assert len(trader.trade_history) == 1
            assert trader.total_traded_today == 0.8
    
    @pytest.mark.asyncio
    async def test_find_and_trade_btc_15m_no_market(self, trader):
        """Test when no BTC market is found"""
        trader.analyzer.get_best_btc_market = AsyncMock(return_value=None)
        
        trade = await trader.find_and_trade_btc_15m()
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_find_and_trade_btc_15m_neutral_signal(self, trader, mock_btc_market):
        """Test when signal is neutral"""
        neutral_signal = MarketSignal(
            market_id=mock_btc_market.id,
            direction='neutral',
            confidence=0.0,
            probability=0.5,
            timestamp=datetime.now(),
            price_history=[]
        )
        
        trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_btc_market)
        trader.analyzer.start_watching_market = AsyncMock(return_value=neutral_signal)
        
        trade = await trader.find_and_trade_btc_15m()
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_find_and_trade_btc_15m_low_probability(self, trader, mock_btc_market):
        """Test when probability is below threshold"""
        low_prob_signal = MarketSignal(
            market_id=mock_btc_market.id,
            direction='up',
            confidence=0.8,
            probability=0.5,  # Below 0.7 threshold
            timestamp=datetime.now(),
            price_history=[]
        )
        
        trader.analyzer.get_best_btc_market = AsyncMock(return_value=mock_btc_market)
        trader.analyzer.start_watching_market = AsyncMock(return_value=low_prob_signal)
        
        trade = await trader.find_and_trade_btc_15m()
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_execute_trade_success(self, trader, mock_btc_market, mock_market_signal, mock_tokens):
        """Test successful trade execution"""
        trader.client.get_market_prices = AsyncMock(return_value=mock_tokens)
        
        with patch.object(trader, '_execute_onchain_trade') as mock_onchain:
            mock_onchain.return_value = '0x1234567890abcdef'
            
            trade = await trader._execute_trade(mock_btc_market, mock_market_signal)
            
            assert trade is not None
            assert trade.market_id == mock_btc_market.id
            assert trade.direction == 'up'
            assert trade.amount == 0.8
            assert trade.price == 0.75
            assert trade.tx_hash == '0x1234567890abcdef'
            assert trade.status == 'confirmed'
    
    @pytest.mark.asyncio
    async def test_execute_trade_no_target_token(self, trader, mock_btc_market, mock_market_signal):
        """Test when target token is not found"""
        # Return tokens without the expected direction
        wrong_tokens = [
            Token('token_side', 'Side', 0.5, 0.5, 1000)
        ]
        
        trader.client.get_market_prices = AsyncMock(return_value=wrong_tokens)
        
        trade = await trader._execute_trade(mock_btc_market, mock_market_signal)
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_execute_trade_limit_reached(self, trader, mock_btc_market, mock_market_signal, mock_tokens):
        """Test when daily trade limit is reached"""
        # Set traded amount to max
        trader.total_traded_today = Config.MAX_TRADE_AMOUNT
        
        trader.client.get_market_prices = AsyncMock(return_value=mock_tokens)
        
        trade = await trader._execute_trade(mock_btc_market, mock_market_signal)
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_execute_trade_partial_limit(self, trader, mock_btc_market, mock_market_signal, mock_tokens):
        """Test when partial limit remains"""
        # Set traded amount close to max
        trader.total_traded_today = Config.MAX_TRADE_AMOUNT - 0.5
        
        trader.client.get_market_prices = AsyncMock(return_value=mock_tokens)
        
        with patch.object(trader, '_execute_onchain_trade') as mock_onchain:
            mock_onchain.return_value = '0x1234567890abcdef'
            
            trade = await trader._execute_trade(mock_btc_market, mock_market_signal)
            
            assert trade is not None
            assert trade.amount == 0.5  # Should use remaining limit
    
    @pytest.mark.asyncio
    async def test_execute_onchain_trade(self, trader):
        """Test on-chain trade execution"""
        token = Token('token_up', 'Up', 0.75, 0.75, 1000)
        amount = 0.8
        
        # Mock Web3 components
        mock_web3 = MagicMock()
        mock_web3.eth.get_transaction_count.return_value = 1
        mock_web3.eth.gas_price = 1000000000  # 1 gwei
        mock_web3.eth.account.sign_transaction.return_value.rawTransaction = b'signed_tx'
        mock_web3.eth.send_raw_transaction.return_value = b'tx_hash'
        
        mock_receipt = MagicMock()
        mock_receipt.status = 1
        mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        
        trader.web3 = mock_web3
        
        with patch.dict(os.environ, {'PRIVATE_KEY': '0x1234567890123456789012345678901234567890123456789012345678901234'}):
            tx_hash = await trader._execute_onchain_trade(token, amount)
            
            assert tx_hash == '747868617368'  # hex of b'tx_hash'
    
    def test_get_trade_summary(self, trader):
        """Test trade summary calculation"""
        # Add some mock trades
        trades = [
            Trade('trade1', 'market1', 'up', 0.8, 0.75, 0.75, datetime.now(), status='confirmed'),
            Trade('trade2', 'market2', 'down', 0.6, 0.65, 0.65, datetime.now(), status='confirmed'),
            Trade('trade3', 'market3', 'up', 0.4, 0.70, 0.70, datetime.now(), status='pending'),  # Should not count
        ]
        
        trader.trade_history = trades
        
        summary = trader.get_trade_summary()
        
        assert summary['total_trades'] == 2  # Only confirmed trades
        assert summary['total_amount'] == 1.4  # 0.8 + 0.6
        assert summary['up_trades'] == 1
        assert summary['down_trades'] == 1
        assert summary['average_probability'] == 0.7  # (0.75 + 0.65) / 2
    
    @pytest.mark.asyncio
    async def test_run_trading_cycle(self, trader):
        """Test trading cycle execution"""
        with patch.object(trader, 'find_and_trade_btc_15m') as mock_find:
            mock_find.return_value = None
            
            await trader.run_trading_cycle()
            
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, trader):
        """Test cleanup functionality"""
        trader.client = AsyncMock()
        
        await trader.cleanup()
        
        trader.client.__aexit__.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
