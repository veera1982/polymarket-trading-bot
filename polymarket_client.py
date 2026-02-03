import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from config import Config

logger = logging.getLogger('polymarket_bot')

@dataclass
class Market:
    """Market data structure"""
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

@dataclass
class Token:
    """Token data structure"""
    id: str
    outcome: str
    price: float
    probability: float
    supply: float

class PolymarketClient:
    """Polymarket API client with self-healing capabilities"""
    
    def __init__(self):
        self.base_url = Config.POLYMARKET_API_URL
        self.graphql_url = Config.POLYMARKET_GRAPHQL_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_connection_time = 0
        self.connection_retry_delay = 5
        self.max_retries = 3
        
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
                    headers={'User-Agent': 'PolymarketTradingBot/1.0'}
                )
                self.last_connection_time = time.time()
                logger.info("Created new Polymarket API session")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise
    
    async def _make_request(self, url: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Make HTTP request with retry logic and self-healing"""
        await self._ensure_session()
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.warning(f"HTTP {response.status} from {url}")
                elif method == 'POST':
                    async with self.session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.warning(f"HTTP {response.status} from {url}")
                            
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
    
    async def get_active_markets(self) -> List[Market]:
        """Fetch all active markets from Polymarket"""
        try:
            # Fetch markets with higher limit to get crypto markets
            url = f"{self.base_url}/markets?limit=500"
            
            logger.debug(f"Fetching markets from: {url}")
            data = await self._make_request(url)
            
            if not data:
                raise Exception("Could not fetch markets from API")
            
            markets = []
            for market_data in data:
                try:
                    if market_data.get('active', False):
                        market = Market(
                            id=market_data['id'],
                            question=market_data['question'],
                            description=market_data.get('description', ''),
                            end_date=market_data.get('endDate') or market_data.get('end_date') or '',
                            active=market_data['active'],
                            volume=float(market_data.get('volume', 0)),
                            liquidity=float(market_data.get('liquidity', 0)),
                            tokens=market_data.get('tokens', []),
                            created_at=market_data.get('createdAt') or market_data.get('created_at') or '',
                            slug=market_data.get('slug', '')
                        )
                        markets.append(market)
                except KeyError as ke:
                    logger.debug(f"Skipping market due to missing field {ke}: {market_data.get('question', 'Unknown')}")
                    continue
            
            logger.info(f"Retrieved {len(markets)} active markets")
            return markets
            
        except Exception as e:
            logger.error(f"Failed to fetch active markets: {e}")
            raise
    
    async def _scrape_current_btc_15m_slug(self) -> Optional[str]:
        """Scrape the current BTC 15m market slug from Polymarket website"""
        try:
            url = "https://polymarket.com/crypto/15M"
            logger.info(f"Scraping current BTC 15m market from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for event URLs in the HTML
                    # Format: /event/btc-updown-15m-{timestamp}
                    import re
                    pattern = r'/event/(btc-updown-15m-\d+)'
                    matches = re.findall(pattern, html)
                    
                    if matches:
                        # Get the most recent (first) match
                        slug = matches[0]
                        logger.info(f"✓ Found current BTC 15m market slug: {slug}")
                        return slug
                    else:
                        logger.warning("Could not find BTC 15m market slug in HTML")
                        return None
                else:
                    logger.warning(f"Failed to fetch Polymarket crypto page: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to scrape current BTC 15m slug: {e}")
            return None
    
    async def get_btc_15m_markets(self) -> List[Market]:
        """Find active 15-minute BTC markets by scraping the Polymarket website"""
        try:
            crypto_15m_markets = []
            
            # Scrape the current market slug from the website
            event_slug = await self._scrape_current_btc_15m_slug()
            
            if not event_slug:
                logger.warning("Could not find current BTC 15m market slug")
                return []
            
            logger.info(f"Using BTC 15m market slug: {event_slug}")
            
            # Create a Market object with the scraped slug
            # Since we can't get full market data from the API, we'll create a minimal Market object
            # The actual trading will use the slug to fetch prices from the website
            market = Market(
                id=event_slug,
                question="Bitcoin Up or Down - 15 minute",
                description="Will Bitcoin price go up or down in the next 15 minutes?",
                end_date="",  # Will be determined from the slug timestamp
                active=True,
                volume=0.0,  # Not available without API
                liquidity=0.0,  # Not available without API
                tokens=[],  # Will be populated when fetching prices
                created_at="",
                slug=event_slug
            )
            
            crypto_15m_markets.append(market)
            logger.info(f"✓ Found BTC 15m market: {market.question} | Slug: {event_slug}")
            
            logger.info(f"Found {len(crypto_15m_markets)} active BTC 15m markets")
            return crypto_15m_markets
            
        except Exception as e:
            logger.error(f"Failed to find 15m crypto markets: {e}")
            raise
    
    async def get_market_by_slug(self, slug: str) -> Optional[Market]:
        """Get a specific market by its slug"""
        try:
            url = f"{self.base_url}/markets?slug={slug}"
            data = await self._make_request(url)
            
            if data and len(data) > 0:
                market_data = data[0]
                market = Market(
                    id=market_data['id'],
                    question=market_data['question'],
                    description=market_data.get('description', ''),
                    end_date=market_data.get('endDate') or market_data.get('end_date') or '',
                    active=market_data.get('active', False),
                    volume=float(market_data.get('volume', 0)),
                    liquidity=float(market_data.get('liquidity', 0)),
                    tokens=market_data.get('tokens', []),
                    created_at=market_data.get('createdAt') or market_data.get('created_at') or '',
                    slug=market_data.get('slug', '')
                )
                logger.info(f"Found market by slug {slug}: {market.question}")
                return market
            return None
        except Exception as e:
            logger.error(f"Failed to get market by slug {slug}: {e}")
            return None
    
    async def get_market_prices(self, market_id: str) -> List[Token]:
        """Get current prices and probabilities for a market"""
        try:
            # Use the correct endpoint without /tokens suffix
            url = f"{self.base_url}/markets/{market_id}"
            market_data = await self._make_request(url)
            
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
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get market prices for {market_id}: {e}")
            raise
    
    async def get_market_history(self, market_id: str, hours: int = 1) -> List[Dict]:
        """Get historical price data for a market"""
        try:
            # This would typically use GraphQL or another endpoint
            # For now, we'll simulate with current data
            # In a real implementation, you'd fetch actual historical data
            url = f"{self.graphql_url}"
            
            query = """
            query {
                market(id: "%s") {
                    tokens {
                        id
                        outcome
                        priceHistory(first: 100, orderBy: timestamp, orderDirection: desc) {
                            timestamp
                            price
                        }
                    }
                }
            }
            """ % market_id
            
            data = await self._make_request(url, method='POST', data={'query': query})
            return data.get('data', {}).get('market', {}).get('tokens', [])
            
        except Exception as e:
            logger.error(f"Failed to get market history for {market_id}: {e}")
            # Return empty list if history fetch fails
            return []
    
    async def health_check(self) -> bool:
        """Check if Polymarket API is accessible"""
        try:
            await self._ensure_session()
            url = f"{self.base_url}/markets"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
