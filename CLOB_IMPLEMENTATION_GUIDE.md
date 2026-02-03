# CLOB Integration Implementation Guide

## Overview

This guide documents the integration of Polymarket's CLOB (Central Limit Order Book) API into the trading bot. The CLOB API provides access to 15-minute cryptocurrency markets for high-frequency trading.

## Architecture

### Current Implementation

```
trading_bot.py (Main orchestrator)
    ↓
trader.py (Uses ClobClient)
    ↓
clob_client.py (HTTP-based CLOB API wrapper)
    ↓
https://clob.polymarket.com (CLOB API)
```

### Key Components

1. **clob_client.py**: Custom HTTP-based CLOB client
   - Async/await support with aiohttp
   - Self-healing connection management
   - Market caching (5-minute TTL)
   - Private key authentication
   - Order signing with HMAC-SHA256

2. **trader.py**: Trading logic
   - Uses ClobClient for market data
   - Executes trades via CLOB API
   - Manages trade history

3. **market_analyzer.py**: Market analysis
   - Analyzes price movements
   - Generates trading signals
   - Uses ClobClient for data

## CLOB API Specification

### Supported Markets

- **Market Type**: 15-minute binary (Up/Down) cryptocurrency markets
- **Assets**: BTC, ETH, SOL, XRP
- **Settlement**: Chainlink for near-instant settlement
- **API Function**: `get_all_15m_markets()`

### Market Discovery

Markets are discovered dynamically using the `get_all_15m_markets()` function:

```python
from clob_client import ClobClient

client = ClobClient()
markets = await client.get_all_15m_markets()

for market in markets:
    print(f"{market.asset_type.upper()}: {market.question}")
    print(f"  ID: {market.id}")
    print(f"  Volume: {market.volume}")
```

### Market Structure

Each market contains:

```python
@dataclass
class Market:
    id: str                          # Unique market identifier
    question: str                    # Market question (e.g., "Bitcoin Up or Down - 15 minute")
    description: str                 # Market description
    end_date: str                    # Market expiration date
    active: bool                     # Whether market is active
    volume: float                    # Trading volume
    liquidity: float                 # Available liquidity
    tokens: List[Dict[str, Any]]    # Token data (UP/DOWN outcomes)
    created_at: str                  # Creation timestamp
    slug: str                        # Market slug
    asset_type: str                  # BTC, ETH, SOL, XRP
    market_type: str                 # 15m
```

### API Methods

#### 1. Get All 15-Minute Markets

```python
markets = await client.get_all_15m_markets()
```

Returns a list of all active 15-minute markets, filtered by asset type and market type.

#### 2. Get Market by ID

```python
market = await client.get_market_by_id(market_id)
```

Retrieve specific market details by ID.

#### 3. Get Market Prices

```python
tokens = await client.get_market_prices(market_id)
```

Get current prices and probabilities for market outcomes.

Returns:
```python
[
    Token(
        id="token_id",
        outcome="UP",
        price=0.65,
        probability=0.65,
        supply=1000.0
    ),
    Token(
        id="token_id",
        outcome="DOWN",
        price=0.35,
        probability=0.35,
        supply=1000.0
    )
]
```

#### 4. Get Market History

```python
history = await client.get_market_history(market_id, limit=100)
```

Retrieve historical price data for a market.

#### 5. Place Order

```python
order = await client.place_order(
    market_id="market_id",
    outcome="UP",  # or "DOWN"
    amount=10.0,
    price=0.65
)
```

Place a trade order on the CLOB.

## Configuration

### Environment Variables

Required in `.env` file:

```bash
# Ethereum wallet credentials
PRIVATE_KEY=your_private_key_here
WALLET_ADDRESS=0xYourWalletAddress

# CLOB API Configuration
POLYMARKET_API_URL=https://clob.polymarket.com
```

### Config File (config.py)

```python
class Config:
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
    POLYMARKET_API_URL = os.getenv('POLYMARKET_API_URL', 'https://clob.polymarket.com')
```

## Implementation Details

### Market Filtering

The `_is_15m_market()` method identifies 15-minute markets by:

1. Checking for "15" and "minute" in the question
2. Verifying presence of crypto asset (BTC, ETH, SOL, XRP)
3. Confirming binary Up/Down structure

### Market Caching

- Markets are cached for 5 minutes
- Cache is automatically invalidated after TTL
- Manual cache refresh available via `get_all_15m_markets()`

### Error Handling

- Automatic retry with exponential backoff
- Rate limit handling (429 responses)
- Connection self-healing on failures
- Detailed error logging

### Authentication

Orders are signed using HMAC-SHA256:

```python
def _sign_order(self, order_data: Dict) -> str:
    message = json.dumps(order_data, sort_keys=True)
    signature = hmac.new(
        self.private_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

## Usage Examples

### Example 1: Discover and Monitor Markets

```python
import asyncio
from clob_client import ClobClient

async def monitor_markets():
    client = ClobClient()
    
    try:
        # Get all 15-minute markets
        markets = await client.get_all_15m_markets()
        
        print(f"Found {len(markets)} 15-minute markets:")
        for market in markets:
            print(f"\n{market.asset_type.upper()}: {market.question}")
            print(f"  ID: {market.id}")
            
            # Get current prices
            tokens = await client.get_market_prices(market.id)
            for token in tokens:
                print(f"  {token.outcome}: ${token.price:.4f}")
    
    finally:
        await client.close()

asyncio.run(monitor_markets())
```

### Example 2: Place a Trade

```python
async def place_trade():
    client = ClobClient()
    
    try:
        # Get markets
        markets = await client.get_all_15m_markets()
        btc_market = next(m for m in markets if m.asset_type == 'btc')
        
        # Place order
        order = await client.place_order(
            market_id=btc_market.id,
            outcome="UP",
            amount=5.0,
            price=0.65
        )
        
        print(f"Order placed: {order}")
    
    finally:
        await client.close()

asyncio.run(place_trade())
```

## Testing

### Unit Tests

Run the test suite:

```bash
python3 -m pytest tests/ -v
```

### Integration Tests

Test CLOB API integration:

```bash
python3 test_clob_integration.py
```

### Manual Testing

Test specific endpoints:

```bash
python3 test_clob_endpoints.py
```

## Troubleshooting

### Issue: HTTP 404 Errors

**Cause**: CLOB API endpoints may not be publicly accessible or require authentication.

**Solution**: 
- Verify API endpoint URLs
- Check network connectivity
- Ensure proper authentication headers

### Issue: Market Data Not Updating

**Cause**: Cache may be stale or API connection lost.

**Solution**:
- Wait for cache expiry (5 minutes)
- Manually refresh by calling `get_all_15m_markets()` again
- Check connection health with `health_check()`

### Issue: Order Placement Fails

**Cause**: Missing or invalid authentication credentials.

**Solution**:
- Verify `PRIVATE_KEY` and `WALLET_ADDRESS` in `.env`
- Ensure wallet has sufficient balance
- Check order parameters (amount, price)

## Performance Considerations

1. **Market Caching**: 5-minute TTL reduces API calls
2. **Async Operations**: Non-blocking I/O for better throughput
3. **Connection Pooling**: Reuses HTTP connections
4. **Exponential Backoff**: Reduces load during failures

## Security Considerations

1. **Private Key Storage**: Keep private keys in `.env` file (never commit)
2. **HTTPS Only**: All API calls use HTTPS
3. **Order Signing**: HMAC-SHA256 for order authentication
4. **Rate Limiting**: Respects API rate limits

## Future Enhancements

1. **WebSocket Support**: Real-time market data via WebSocket
2. **Advanced Order Types**: Limit orders, stop-loss, etc.
3. **Portfolio Management**: Track positions and P&L
4. **Risk Management**: Position sizing, drawdown limits
5. **Backtesting**: Historical data analysis

## References

- [Polymarket Documentation](https://docs.polymarket.com)
- [CLOB API Specification](https://docs.polymarket.com/api)
- [py-clob-client GitHub](https://github.com/Polymarket/py-clob-client)
- [15-Minute Markets](https://polymarket.com/crypto/15M)

## Support

For issues or questions:

1. Check the [Polymarket Discord](https://discord.gg/polymarket)
2. Review [GitHub Issues](https://github.com/discountry/polymarket-trading-bot/issues)
3. Consult the [API Documentation](https://docs.polymarket.com)
