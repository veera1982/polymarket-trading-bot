# Polymarket CLOB API Reference

**Last Updated:** February 3, 2026  
**API Version:** py-clob-client v0.34.5  
**Base URL:** https://clob.polymarket.com

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Structures](#data-structures)
5. [Code Examples](#code-examples)
6. [Error Handling](#error-handling)

---

## 🌐 Overview

### CLOB API
The Central Limit Order Book (CLOB) API is Polymarket's official trading interface. It provides:
- Real-time market data
- Order placement and management
- Position tracking
- Trade history

### Key Features
- **WebSocket Support:** Real-time orderbook updates
- **REST API:** Market data and order management
- **Authentication:** Private key signing
- **Rate Limits:** Generous limits for market makers

---

## 🔐 Authentication

### Private Key Setup

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client with authentication
host = "https://clob.polymarket.com"
key = os.getenv("PRIVATE_KEY")  # Without 0x prefix
chain_id = 137  # Polygon mainnet

# Create credentials
creds = ApiCreds(
    api_key=key,
    api_secret=key,
    api_passphrase=""
)

# Initialize client
client = ClobClient(host, key=key, chain_id=chain_id, creds=creds)
```

### Signature Generation

The API uses HMAC-SHA256 for request signing:

```python
import hmac
import hashlib
import time

def sign_request(private_key, timestamp, method, path, body=""):
    """Sign API request"""
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        private_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

---

## 🔌 API Endpoints

### Market Data

#### Get All Markets

```python
# Fetch all markets
markets = client.get_markets()

# Response structure
{
    "data": [
        {
            "condition_id": "0x123...",
            "question": "Will BTC be up in 15 minutes?",
            "active": true,
            "closed": false,
            "archived": false,
            "accepting_orders": true,
            "enable_order_book": true,
            "description": "...",
            "end_date_iso": "2026-02-03T11:00:00Z",
            "tokens": [
                {
                    "token_id": "123",
                    "outcome": "Yes",
                    "price": "0.52"
                },
                {
                    "token_id": "124",
                    "outcome": "No",
                    "price": "0.48"
                }
            ]
        }
    ],
    "next_cursor": "cursor_string",
    "limit": 100,
    "count": 1000
}
```

#### Get Market by ID

```python
# Fetch specific market
market = client.get_market(condition_id="0x123...")

# Response: Single market object (same structure as above)
```

#### Get Orderbook

```python
# Fetch orderbook for a token
orderbook = client.get_order_book(token_id="123")

# Response structure
{
    "bids": [
        {
            "price": "0.51",
            "size": "100.0"
        },
        {
            "price": "0.50",
            "size": "250.0"
        }
    ],
    "asks": [
        {
            "price": "0.52",
            "size": "150.0"
        },
        {
            "price": "0.53",
            "size": "200.0"
        }
    ]
}
```

#### Get Market Prices

```python
# Get current prices for market
prices = client.get_prices(condition_id="0x123...")

# Response structure
{
    "tokens": [
        {
            "token_id": "123",
            "price": "0.52",
            "volume_24h": "10000.0"
        },
        {
            "token_id": "124",
            "price": "0.48",
            "volume_24h": "10000.0"
        }
    ]
}
```

### Trading

#### Place Order

```python
from py_clob_client.order_builder.constants import BUY, SELL

# Create buy order
order = client.create_order(
    token_id="123",
    price=0.51,
    size=100.0,
    side=BUY,
    order_type="GTC"  # Good Till Cancelled
)

# Response structure
{
    "order_id": "order_123",
    "status": "LIVE",
    "created_at": "2026-02-03T10:00:00Z",
    "token_id": "123",
    "price": "0.51",
    "size": "100.0",
    "side": "BUY",
    "filled_size": "0.0"
}
```

#### Cancel Order

```python
# Cancel specific order
result = client.cancel_order(order_id="order_123")

# Response
{
    "order_id": "order_123",
    "status": "CANCELLED"
}
```

#### Get Open Orders

```python
# Fetch all open orders
orders = client.get_orders()

# Response structure
{
    "data": [
        {
            "order_id": "order_123",
            "token_id": "123",
            "price": "0.51",
            "size": "100.0",
            "filled_size": "25.0",
            "side": "BUY",
            "status": "LIVE"
        }
    ]
}
```

### Account

#### Get Balances

```python
# Fetch account balances
balances = client.get_balances()

# Response structure
{
    "balances": [
        {
            "asset": "USDC",
            "total": "1000.0",
            "available": "900.0",
            "locked": "100.0"
        }
    ]
}
```

#### Get Positions

```python
# Fetch current positions
positions = client.get_positions()

# Response structure
{
    "positions": [
        {
            "market_id": "0x123...",
            "token_id": "123",
            "size": "100.0",
            "avg_price": "0.50",
            "current_price": "0.52",
            "pnl": "2.0"
        }
    ]
}
```

#### Get Trade History

```python
# Fetch trade history
trades = client.get_trades()

# Response structure
{
    "data": [
        {
            "trade_id": "trade_123",
            "order_id": "order_123",
            "token_id": "123",
            "price": "0.51",
            "size": "25.0",
            "side": "BUY",
            "timestamp": "2026-02-03T10:05:00Z",
            "fee": "0.025"
        }
    ]
}
```

---

## 📊 Data Structures

### Market Object

```python
{
    "condition_id": str,          # Unique market identifier
    "question": str,              # Market question
    "description": str,           # Detailed description
    "active": bool,               # Market is active
    "closed": bool,               # Trading closed
    "archived": bool,             # Market archived
    "accepting_orders": bool,     # Accepting new orders
    "enable_order_book": bool,    # Orderbook enabled
    "end_date_iso": str,          # Market end date (ISO 8601)
    "tokens": [                   # Outcome tokens
        {
            "token_id": str,
            "outcome": str,       # "Yes" or "No"
            "price": str,         # Current price (0-1)
            "volume_24h": str     # 24h volume
        }
    ],
    "volume": str,                # Total volume
    "liquidity": str              # Available liquidity
}
```

### Order Object

```python
{
    "order_id": str,              # Unique order ID
    "token_id": str,              # Token being traded
    "price": str,                 # Order price (0-1)
    "size": str,                  # Order size (USDC)
    "filled_size": str,           # Amount filled
    "side": str,                  # "BUY" or "SELL"
    "status": str,                # "LIVE", "FILLED", "CANCELLED"
    "order_type": str,            # "GTC", "FOK", "IOC"
    "created_at": str,            # Creation timestamp
    "updated_at": str             # Last update timestamp
}
```

### Trade Object

```python
{
    "trade_id": str,              # Unique trade ID
    "order_id": str,              # Associated order ID
    "token_id": str,              # Token traded
    "price": str,                 # Execution price
    "size": str,                  # Trade size
    "side": str,                  # "BUY" or "SELL"
    "timestamp": str,             # Execution time
    "fee": str,                   # Trading fee
    "maker": bool                 # Maker or taker
}
```

---

## 💻 Code Examples

### Example 1: Fetch 15-Minute Crypto Markets

```python
from py_clob_client.client import ClobClient

def get_15min_crypto_markets():
    """Fetch all 15-minute crypto markets"""
    client = ClobClient("https://clob.polymarket.com")
    
    # Fetch all markets
    response = client.get_markets()
    markets = response.get("data", [])
    
    # Filter for 15-minute crypto markets
    crypto_assets = ["BTC", "ETH", "SOL", "XRP"]
    filtered_markets = []
    
    for market in markets:
        question = market.get("question", "").lower()
        
        # Check for 15-minute timeframe
        if "15" in question and "minute" in question:
            # Check for crypto assets
            for asset in crypto_assets:
                if asset.lower() in question:
                    filtered_markets.append(market)
                    break
    
    return filtered_markets

# Usage
markets = get_15min_crypto_markets()
print(f"Found {len(markets)} 15-minute crypto markets")
```

### Example 2: Place Arbitrage Trade

```python
from py_clob_client.client import ClobClient
from py_clob_client.order_builder.constants import BUY, SELL

def execute_arbitrage(client, market):
    """Execute arbitrage trade if opportunity exists"""
    
    # Get token prices
    yes_token = market["tokens"][0]
    no_token = market["tokens"][1]
    
    yes_price = float(yes_token["price"])
    no_price = float(no_token["price"])
    
    # Check for arbitrage (total probability < 1.0)
    total_prob = yes_price + no_price
    
    if total_prob < 0.98:  # 2% threshold
        # Buy both outcomes
        size = 100.0  # $100 USDC
        
        # Place orders
        yes_order = client.create_order(
            token_id=yes_token["token_id"],
            price=yes_price,
            size=size,
            side=BUY
        )
        
        no_order = client.create_order(
            token_id=no_token["token_id"],
            price=no_price,
            size=size,
            side=BUY
        )
        
        profit = size * (1.0 - total_prob)
        print(f"✅ Arbitrage executed! Expected profit: ${profit:.2f}")
        
        return yes_order, no_order
    
    return None

# Usage
client = ClobClient("https://clob.polymarket.com", key="your_key")
markets = get_15min_crypto_markets()

for market in markets:
    result = execute_arbitrage(client, market)
```

### Example 3: Monitor Market Prices

```python
import time
from py_clob_client.client import ClobClient

def monitor_market(client, condition_id, interval=60):
    """Monitor market prices in real-time"""
    
    print(f"Monitoring market {condition_id}...")
    
    while True:
        try:
            # Fetch current prices
            market = client.get_market(condition_id)
            
            for token in market["tokens"]:
                outcome = token["outcome"]
                price = float(token["price"])
                volume = float(token.get("volume_24h", 0))
                
                print(f"{outcome}: ${price:.4f} | Volume: ${volume:.2f}")
            
            # Wait before next check
            time.sleep(interval)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval)

# Usage
client = ClobClient("https://clob.polymarket.com")
monitor_market(client, "0x123...", interval=30)
```

### Example 4: Risk Management

```python
def check_position_risk(client, max_position_size=1000.0, max_risk_pct=0.05):
    """Check if position is within risk limits"""
    
    # Get current positions
    positions = client.get_positions()
    
    total_exposure = 0.0
    risky_positions = []
    
    for position in positions.get("positions", []):
        size = float(position["size"])
        avg_price = float(position["avg_price"])
        current_price = float(position["current_price"])
        
        # Calculate exposure
        exposure = size * avg_price
        total_exposure += exposure
        
        # Calculate unrealized P&L
        pnl = size * (current_price - avg_price)
        pnl_pct = pnl / exposure if exposure > 0 else 0
        
        # Check risk limits
        if exposure > max_position_size:
            risky_positions.append({
                "market_id": position["market_id"],
                "reason": "Position size exceeded",
                "exposure": exposure,
                "limit": max_position_size
            })
        
        if abs(pnl_pct) > max_risk_pct:
            risky_positions.append({
                "market_id": position["market_id"],
                "reason": "Risk percentage exceeded",
                "pnl_pct": pnl_pct,
                "limit": max_risk_pct
            })
    
    return {
        "total_exposure": total_exposure,
        "risky_positions": risky_positions,
        "within_limits": len(risky_positions) == 0
    }

# Usage
client = ClobClient("https://clob.polymarket.com", key="your_key")
risk_check = check_position_risk(client)

if not risk_check["within_limits"]:
    print("⚠️ Risk limits exceeded!")
    for position in risk_check["risky_positions"]:
        print(f"  - {position['reason']}: {position['market_id']}")
```

---

## ⚠️ Error Handling

### Common Errors

```python
from py_clob_client.exceptions import PolymarketAPIException

try:
    # API call
    markets = client.get_markets()
    
except PolymarketAPIException as e:
    if e.status_code == 401:
        print("❌ Authentication failed - check private key")
    elif e.status_code == 429:
        print("❌ Rate limit exceeded - wait before retrying")
    elif e.status_code == 404:
        print("❌ Market not found")
    elif e.status_code == 500:
        print("❌ Server error - try again later")
    else:
        print(f"❌ API error: {e}")
        
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Retry Logic

```python
import time
from functools import wraps

def retry_on_error(max_retries=3, delay=1.0, backoff=2.0):
    """Decorator for retrying failed API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    
                    print(f"⚠️ Error: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator

# Usage
@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def fetch_markets(client):
    return client.get_markets()

# Will retry up to 3 times with exponential backoff
markets = fetch_markets(client)
```

---

## 📚 Additional Resources

### Official Documentation
- **CLOB API Docs:** https://docs.polymarket.com/api-reference
- **py-clob-client GitHub:** https://github.com/Polymarket/py-clob-client
- **Market Maker Guide:** https://docs.polymarket.com/market-makers

### Rate Limits
- **Public Endpoints:** 100 requests/minute
- **Authenticated Endpoints:** 300 requests/minute
- **WebSocket Connections:** 10 concurrent connections

### Best Practices
1. Use WebSocket for real-time data
2. Implement exponential backoff for retries
3. Cache market data when possible
4. Monitor rate limits
5. Handle errors gracefully
6. Use proper authentication
7. Validate all inputs
8. Log all API calls

---

**End of API Reference**
