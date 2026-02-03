"""CLOB (Central Limit Order Book) Client for Polymarket

This module provides a direct HTTP-based client for the Polymarket CLOB API.
It replaces the deprecated Gamma API with the official CLOB API endpoints.

API Documentation: https://docs.polymarket.com/
CLOB API Endpoint: https://clob.polymarket.com
"""

import asyncio
import aiohttp
import json
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from config import Config

logger = logging.getLogger('polymarket_bot')

@dataclass
class Market:
    """Market data structure for CLOB API"""
    id: str
    question: str
    description: str
    end_date: str
    active: bool
    volume: float
    liquidity: float
    tokens: List[Dict[str, Any]]
    created_at: str
    slug: str
    asset_type: str = "crypto"  # BTC, ETH, SOL, XRP
    market_type: str = "15m"  # 15-minute markets

@dataclass
class Token:
    """Token data structure"""
    id: str
    outcome: str
    price: float
    probability: float
    supply: float

class ClobClient:
    """Polymarket CLOB API client with authentication and trade execution"""
    
    # CLOB API Configuration
    CLOB_API_URL = "https://clob.polymarket.com"
    CLOB_API_VERSION = "v1"
    
    def __init__(self, private_key: Optional[str] = None, wallet_address: Optional[str] = None):
        """
        Initialize CLOB client with optional authentication
        
        Args:
            private_key: Ethereum private key for trade execution
            wallet_address: Ethereum wallet address
        """
        self.base_url = self.CLOB_API_URL
        self.api_version = self.CLOB_API_VERSION
        self.session: Optional[aiohttp.ClientSession] = None
        self.private_key = private_key or Config.PRIVATE_KEY
        self.wallet_address = wallet_address or Config.WALLET_ADDRESS
        self.last_connection_time = 0
        self.connection_retry_delay = 5
        self.max_retries = 3
        
        # Market cache for 15-minute markets
        self.market_cache: Dict[str, Market] = {}
        self.cache_expiry = 300  # 5 minutes
        self.last_cache_update = 0
        
    async def __aenter__(self):
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure we have an active session with self-healing"""
        if self.session is None or self.session.closed:
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers={
                        'User-Agent': 'PolymarketTradingBot/2.0-CLOB',
                        'Content-Type': 'application/json'
                    }
                )
                self.last_connection_time = time.time()
                logger.info("Created new CLOB API session")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise
    
    async def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None, use_versioning: bool = True) -> Dict:
        """Make HTTP request to CLOB API with retry logic"""
        await self._ensure_session()
        
        # Some endpoints don't use versioning
        if use_versioning:
            url = f"{self.base_url}/{self.api_version}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.warning(f"HTTP {response.status} from {url}")
                            if response.status == 429:  # Rate limited
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                elif method == 'POST':
                    async with self.session.post(url, json=data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            logger.warning(f"HTTP {response.status} from {url}")
                            if response.status == 429:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    # Self-healing: recreate session on connection errors
                    if self.session:
                        await self.session.close()
                    self.session = None
                    await asyncio.sleep(self.connection_retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error("Max retries reached, request failed")
                    raise
        
        raise Exception("Request failed after all retries")
    
    async def get_all_15m_markets(self) -> List[Market]:
        """
        Fetch all active 15-minute crypto markets from CLOB API
        
        This is the primary method for discovering 15-minute markets.
        Returns markets for BTC, ETH, SOL, and XRP.
        
        Returns:
            List of Market objects for 15-minute crypto markets
        """
        try:
            # Check cache first
            if self.market_cache and (time.time() - self.last_cache_update) < self.cache_expiry:
                logger.debug("Using cached 15m markets")
                return list(self.market_cache.values())
            
            logger.info("Fetching 15-minute markets from CLOB API...")
            
            # CLOB API endpoint for markets (try without versioning first)
            endpoint = "/markets"
            try:
                data = await self._make_request(endpoint, use_versioning=False)
            except:
                # Fallback to versioned endpoint
                data = await self._make_request(endpoint, use_versioning=True)
            
            if not data:
                raise Exception("Could not fetch markets from CLOB API")
            
            markets = []
            
            # Filter for 15-minute markets
            for market_data in data.get('markets', []):
                try:
                    # Check if this is a 15-minute market
                    if self._is_15m_market(market_data):
                        market = self._parse_market(market_data)
                        markets.append(market)
                        self.market_cache[market.id] = market
                except Exception as e:
                    logger.debug(f"Skipping market: {e}")
                    continue
            
            self.last_cache_update = time.time()
            logger.info(f"Retrieved {len(markets)} active 15-minute markets")
            return markets
            
        except Exception as e:
            logger.error(f"Failed to fetch 15m markets: {e}")
            raise
    
    def _is_15m_market(self, market_data: Dict) -> bool:
        """
        Check if a market is a 15-minute crypto market
        
        15-minute markets have specific naming patterns:
        - BTC Up or Down - 15 minute
        - ETH Up or Down - 15 minute
        - SOL Up or Down - 15 minute
        - XRP Up or Down - 15 minute
        """
        question = market_data.get('question', '').lower()
        
        # Check for 15-minute market indicators
        is_15m = '15' in question and ('minute' in question or 'min' in question)
        
        # Check for crypto assets
        is_crypto = any(asset in question.upper() for asset in ['BTC', 'ETH', 'SOL', 'XRP'])
        
        # Check for up/down binary market
        is_binary = 'up' in question and 'down' in question
        
        return is_15m and is_crypto and is_binary
    
    def _parse_market(self, market_data: Dict) -> Market:
        """Parse market data from CLOB API response"""
        question = market_data.get('question', '')
        
        # Extract asset type from question
        asset_type = 'unknown'
        for asset in ['BTC', 'ETH', 'SOL', 'XRP']:
            if asset in question.upper():
                asset_type = asset.lower()
                break
        
        market = Market(
            id=market_data.get('id', ''),
            question=question,
            description=market_data.get('description', ''),
            end_date=market_data.get('endDate') or market_data.get('end_date') or '',
            active=market_data.get('active', False),
            volume=float(market_data.get('volume', 0)),
            liquidity=float(market_data.get('liquidity', 0)),
            tokens=market_data.get('tokens', []),
            created_at=market_data.get('createdAt') or market_data.get('created_at') or '',
            slug=market_data.get('slug', ''),
            asset_type=asset_type,
            market_type='15m'
        )
        return market
    
    async def get_market_by_id(self, market_id: str) -> Optional[Market]:
        """
        Get a specific market by its ID
        
        Args:
            market_id: The market ID from CLOB API
            
        Returns:
            Market object or None if not found
        """
        try:
            # Check cache first
            if market_id in self.market_cache:
                return self.market_cache[market_id]
            
            endpoint = f"/markets/{market_id}"
            data = await self._make_request(endpoint)
            
            if data:
                market = self._parse_market(data)
                self.market_cache[market_id] = market
                logger.info(f"Found market {market_id}: {market.question}")
                return market
            return None
        except Exception as e:
            logger.error(f"Failed to get market {market_id}: {e}")
            return None
    
    async def get_market_prices(self, market_id: str) -> List[Token]:
        """
        Get current prices and probabilities for a market
        
        Args:
            market_id: The market ID
            
        Returns:
            List of Token objects with current prices
        """
        try:
            endpoint = f"/markets/{market_id}"
            market_data = await self._make_request(endpoint)
            
            tokens = []
            # Token information is nested within the market object
            token_list = market_data.get('tokens', [])
            if not token_list:
                # Try alternative field name
                token_list = market_data.get('clobTokenIds', [])
            
            for token_data in token_list:
                token = Token(
                    id=token_data.get('id', ''),
                    outcome=token_data.get('outcome', ''),
                    price=float(token_data.get('price', 0)),
                    probability=float(token_data.get('probability', 0)),
                    supply=float(token_data.get('supply', 0))
                )
                tokens.append(token)
            
            logger.debug(f"Retrieved {len(tokens)} tokens for market {market_id}")
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get market prices for {market_id}: {e}")
            raise
    
    async def get_market_history(self, market_id: str, limit: int = 100) -> List[Dict]:
        """
        Get historical price data for a market
        
        Args:
            market_id: The market ID
            limit: Number of historical data points to retrieve
            
        Returns:
            List of historical price data
        """
        try:
            endpoint = f"/markets/{market_id}/history?limit={limit}"
            data = await self._make_request(endpoint)
            
            logger.debug(f"Retrieved {len(data)} historical data points for market {market_id}")
            return data.get('history', [])
            
        except Exception as e:
            logger.error(f"Failed to get market history for {market_id}: {e}")
            return []
    
    async def place_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """
        Place a trade order on the CLOB
        
        Args:
            market_id: The market ID
            outcome: 'YES' or 'NO' (or 'UP' or 'DOWN' for crypto markets)
            amount: Amount to trade
            price: Price per share
            
        Returns:
            Order confirmation data
        """
        try:
            if not self.private_key or not self.wallet_address:
                raise Exception("Private key and wallet address required for trading")
            
            endpoint = "/orders"
            order_data = {
                "market_id": market_id,
                "outcome": outcome,
                "amount": amount,
                "price": price,
                "wallet_address": self.wallet_address
            }
            
            # Sign the order with private key
            signature = self._sign_order(order_data)
            order_data["signature"] = signature
            
            response = await self._make_request(endpoint, method='POST', data=order_data)
            logger.info(f"Order placed: {outcome} {amount} @ {price} on market {market_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def _sign_order(self, order_data: Dict) -> str:
        """
        Sign an order with the private key
        
        Args:
            order_data: The order data to sign
            
        Returns:
            Signature string
        """
        try:
            # Create a message from order data
            message = json.dumps(order_data, sort_keys=True)
            
            # Sign with private key using HMAC-SHA256
            signature = hmac.new(
                self.private_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
        except Exception as e:
            logger.error(f"Failed to sign order: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if CLOB API is accessible
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            await self._ensure_session()
            endpoint = "/health"
            try:
                response = await self._make_request(endpoint, use_versioning=False)
            except:
                response = await self._make_request(endpoint, use_versioning=True)
            is_healthy = response.get('status') == 'ok' or response.get('ok') == True
            
            if is_healthy:
                logger.info("✓ CLOB API health check passed")
            else:
                logger.warning("CLOB API health check failed")
            
            return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def get_btc_15m_markets(self) -> List[Market]:
        """
        Get all active BTC 15-minute markets
        
        Returns:
            List of BTC 15m Market objects
        """
        try:
            all_markets = await self.get_all_15m_markets()
            
            # Filter for BTC markets only
            btc_markets = [m for m in all_markets if m.asset_type.lower() == 'btc']
            
            logger.info(f"Found {len(btc_markets)} active BTC 15-minute markets")
            return btc_markets
            
        except Exception as e:
            logger.error(f"Failed to get BTC 15m markets: {e}")
            return []
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            logger.info("CLOB client session closed")
