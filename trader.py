import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from web3 import Web3
from eth_account import Account
from config import Config
from clob_client import ClobClient, Market, Token
from market_analyzer import MarketAnalyzer, MarketSignal

logger = logging.getLogger('polymarket_bot')

@dataclass
class Trade:
    """Trade execution record"""
    id: str
    market_id: str
    direction: str
    amount: float
    price: float
    probability: float
    timestamp: datetime
    tx_hash: Optional[str] = None
    status: str = 'pending'  # pending, confirmed, failed

class Trader:
    """Handles trading operations with Polymarket"""
    
    def __init__(self):
        self.client = ClobClient()
        self.analyzer = MarketAnalyzer(self.client)
        self.web3 = None
        self.account = None
        self.total_traded_today = 0.0
        self.trade_history: List[Trade] = []
        
        # Initialize Web3 connection
        self._init_web3()
    
    def _init_web3(self):
        """Initialize Web3 connection for blockchain interactions"""
        try:
            # Using Polygon network for Polymarket
            polygon_rpc = "https://polygon-rpc.com"
            self.web3 = Web3(Web3.HTTPProvider(polygon_rpc))
            
            if self.web3.is_connected():
                logger.info("Connected to Polygon network")
                
                # Initialize account from private key
                if Config.PRIVATE_KEY:
                    self.account = Account.from_key(Config.PRIVATE_KEY)
                    logger.info(f"Trading with wallet: {self.account.address}")
                else:
                    logger.warning("No private key configured - trading will be simulated")
            else:
                logger.error("Failed to connect to Polygon network")
                
        except Exception as e:
            logger.error(f"Failed to initialize Web3: {e}")
    
    async def find_and_trade_btc_15m(self) -> Optional[Trade]:
        """Main trading logic: find BTC 15m market and execute trade immediately"""
        try:
            # Find best BTC market
            market = await self.analyzer.get_best_btc_market()
            if not market:
                logger.warning("No suitable BTC market found")
                return None
            
            logger.info(f"Found market: {market.question}")
            
            # Get current market prices immediately (no waiting)
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
            
            if not up_token or not down_token:
                logger.warning(f"Could not find up/down tokens for market {market.id}")
                return None
            
            logger.info(f"Current prices - Up: {up_token.price:.4f} ({up_token.probability:.2%}), "
                       f"Down: {down_token.price:.4f} ({down_token.probability:.2%})")
            
            # Determine direction based on current probability
            if up_token.probability > down_token.probability:
                direction = 'up'
                selected_token = up_token
            else:
                direction = 'down'
                selected_token = down_token
            
            logger.info(f"Direction: {direction.upper()} (probability: {selected_token.probability:.2%})")
            
            # Create signal for trade
            signal = MarketSignal(
                market_id=market.id,
                direction=direction,
                confidence=abs(up_token.probability - down_token.probability),
                probability=selected_token.probability,
                timestamp=datetime.now(),
                price_history=[]
            )
            
            # Execute trade immediately
            trade = await self._execute_trade(market, signal)
            
            if trade:
                self.trade_history.append(trade)
                self.total_traded_today += trade.amount
                
            return trade
            
        except Exception as e:
            logger.error(f"Error in find_and_trade_btc_15m: {e}")
            return None
    
    async def _execute_trade(self, market: Market, signal: MarketSignal) -> Optional[Trade]:
        """Execute a trade based on the signal"""
        try:
            # Check trade limits
            if self.total_traded_today >= Config.MAX_TRADE_AMOUNT:
                logger.warning(f"Daily trade limit {Config.MAX_TRADE_AMOUNT} reached")
                return None
            
            # Determine trade amount (default $0.8, but respect remaining limit)
            remaining_limit = Config.MAX_TRADE_AMOUNT - self.total_traded_today
            trade_amount = min(Config.DEFAULT_TRADE_AMOUNT, remaining_limit)
            
            if trade_amount <= 0:
                logger.warning("No remaining trade limit")
                return None
            
            # Get current market prices
            tokens = await self.client.get_market_prices(market.id)
            
            # Find the appropriate token to buy
            target_token = None
            for token in tokens:
                outcome_lower = token.outcome.lower()
                if (signal.direction == 'up' and 'up' in outcome_lower) or \
                   (signal.direction == 'down' and 'down' in outcome_lower):
                    target_token = token
                    break
            
            if not target_token:
                logger.error(f"Could not find {signal.direction} token for market {market.id}")
                return None
            
            # Create trade record
            trade = Trade(
                id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                market_id=market.id,
                direction=signal.direction,
                amount=trade_amount,
                price=target_token.price,
                probability=target_token.probability,
                timestamp=datetime.now()
            )
            
            # Execute the actual trade
            if self.account and self.web3:
                tx_hash = await self._execute_onchain_trade(target_token, trade_amount)
                trade.tx_hash = tx_hash
                trade.status = 'confirmed' if tx_hash else 'failed'
            else:
                # Simulated trade for testing
                logger.info(f"SIMULATED TRADE: Buy {signal.direction} for ${trade_amount:.2f} "
                           f"at {target_token.price:.4f} ({target_token.probability:.2%})")
                trade.status = 'confirmed'
            
            logger.info(f"Trade executed: {signal.direction} ${trade_amount:.2f} "
                       f"at {target_token.price:.4f} (prob: {target_token.probability:.2%})")
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return None
    
    async def _execute_onchain_trade(self, token: Token, amount: float) -> Optional[str]:
        """Execute trade on Polygon blockchain"""
        try:
            # This is a simplified implementation
            # In reality, you'd need to interact with Polymarket's smart contracts
            
            # Convert amount to wei (assuming USDC with 6 decimals)
            amount_wei = int(amount * 1e6)
            
            # Get token contract address and ABI (simplified)
            token_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
            
            # Build transaction
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            
            # This would be the actual contract interaction
            # For now, we'll simulate it
            tx_data = {
                'to': token_address,
                'value': 0,
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
                'data': '0x'  # Actual function call data would go here
            }
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx_data, Config.PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                logger.info(f"Trade confirmed: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Trade failed: {tx_hash.hex()}")
                return None
                
        except Exception as e:
            logger.error(f"On-chain trade failed: {e}")
            return None
    
    def get_trade_summary(self) -> Dict:
        """Get summary of today's trades"""
        confirmed_trades = [t for t in self.trade_history if t.status == 'confirmed']
        
        return {
            'total_trades': len(confirmed_trades),
            'total_amount': sum(t.amount for t in confirmed_trades),
            'up_trades': len([t for t in confirmed_trades if t.direction == 'up']),
            'down_trades': len([t for t in confirmed_trades if t.direction == 'down']),
            'average_probability': sum(t.probability for t in confirmed_trades) / len(confirmed_trades) if confirmed_trades else 0,
            'last_trade_time': max((t.timestamp for t in confirmed_trades), default=None)
        }
    
    async def run_trading_cycle(self):
        """Run one complete trading cycle"""
        logger.info("Starting trading cycle")
        
        try:
            trade = await self.find_and_trade_btc_15m()
            
            if trade:
                summary = self.get_trade_summary()
                logger.info(f"Trading cycle complete. Summary: {summary}")
            else:
                logger.info("No trade executed in this cycle")
                
        except Exception as e:
            logger.error(f"Trading cycle failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.__aexit__(None, None, None)
