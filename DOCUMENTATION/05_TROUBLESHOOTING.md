# Polymarket Trading Bot - Troubleshooting Guide

**Last Updated:** February 3, 2026  
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Installation Issues](#installation-issues)
2. [API Connection Problems](#api-connection-problems)
3. [Authentication Errors](#authentication-errors)
4. [Market Data Issues](#market-data-issues)
5. [Trading Errors](#trading-errors)
6. [Performance Problems](#performance-problems)
7. [Common Error Messages](#common-error-messages)
8. [FAQ](#faq)

---

## 🔧 Installation Issues

### Problem: Python Version Incompatibility

**Error Message:**
```
ERROR: Package 'py-clob-client' requires a different Python: 3.9.6 not in '>=3.9.10'
```

**Solution:**
```bash
# Install pyenv
brew install pyenv  # macOS
# OR
curl https://pyenv.run | bash  # Linux

# Install Python 3.11.0
pyenv install 3.11.0

# Set local version
cd ~/CascadeProjects/polymarket-trading-bot
pyenv local 3.11.0

# Verify
python --version
# Should show: Python 3.11.0

# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install git+https://github.com/Polymarket/py-clob-client.git
```

### Problem: pip Install Fails

**Error Message:**
```
ERROR: Could not find a version that satisfies the requirement py-clob-client
```

**Solution:**
```bash
# py-clob-client is not on PyPI, install from GitHub
pip install git+https://github.com/Polymarket/py-clob-client.git

# If git is not installed
brew install git  # macOS
sudo apt-get install git  # Linux

# Verify installation
python -c "from py_clob_client.client import ClobClient; print('Success')"
```

### Problem: Virtual Environment Not Activating

**Error Message:**
```
bash: venv/bin/activate: No such file or directory
```

**Solution:**
```bash
# Ensure you're in the correct directory
cd ~/CascadeProjects/polymarket-trading-bot

# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation (should show venv in prompt)
which python
# Should show: /path/to/polymarket-trading-bot/venv/bin/python
```

### Problem: Permission Denied

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages'
```

**Solution:**
```bash
# Don't use sudo with pip in virtual environment
# Instead, ensure virtual environment is activated
source venv/bin/activate

# Then install packages
pip install git+https://github.com/Polymarket/py-clob-client.git

# If still having issues, recreate venv
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
```

---

## 🌐 API Connection Problems

### Problem: Cannot Connect to CLOB API

**Error Message:**
```
ConnectionError: Failed to connect to clob.polymarket.com
```

**Solution:**
```bash
# 1. Check internet connection
ping clob.polymarket.com

# 2. Check if API is accessible
curl https://clob.polymarket.com/markets

# 3. Verify firewall settings
# Ensure port 443 (HTTPS) is not blocked

# 4. Try with different network
# Use mobile hotspot or different WiFi

# 5. Check API status
# Visit https://status.polymarket.com
```

### Problem: Timeout Errors

**Error Message:**
```
TimeoutError: Request timed out after 30 seconds
```

**Solution:**
```python
# Increase timeout in client initialization
from py_clob_client.client import ClobClient

client = ClobClient(
    "https://clob.polymarket.com",
    timeout=60  # Increase to 60 seconds
)

# Or implement retry logic
import time
from functools import wraps

def retry_on_timeout(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except TimeoutError:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
        return wrapper
    return decorator

@retry_on_timeout(max_retries=3)
def fetch_markets(client):
    return client.get_markets()
```

### Problem: SSL Certificate Errors

**Error Message:**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solution:**
```bash
# Update SSL certificates (macOS)
/Applications/Python\ 3.11/Install\ Certificates.command

# Update SSL certificates (Linux)
sudo apt-get update
sudo apt-get install ca-certificates

# Update certifi package
pip install --upgrade certifi

# If still failing, check system time
date
# Ensure system time is correct
```

---

## 🔐 Authentication Errors

### Problem: Invalid Private Key

**Error Message:**
```
ValueError: Invalid private key format
```

**Solution:**
```bash
# 1. Check .env file format
cat .env | grep PRIVATE_KEY

# Should look like:
# PRIVATE_KEY=abc123def456...  (NO 0x prefix)

# 2. Remove 0x prefix if present
# Wrong: PRIVATE_KEY=0xabc123...
# Right: PRIVATE_KEY=abc123...

# 3. Ensure no spaces or quotes
# Wrong: PRIVATE_KEY = "abc123..."
# Right: PRIVATE_KEY=abc123...

# 4. Verify key length (64 characters for hex)
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('PRIVATE_KEY')
print(f'Key length: {len(key)}')
print(f'Valid: {len(key) == 64}')
"
```

### Problem: Authentication Failed

**Error Message:**
```
401 Unauthorized: Authentication failed
```

**Solution:**
```python
# 1. Verify private key is correct
from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv()
private_key = os.getenv('PRIVATE_KEY')

# Add 0x prefix for verification
account = Account.from_key('0x' + private_key)
print(f"Wallet address: {account.address}")

# Compare with your expected wallet address
expected = os.getenv('WALLET_ADDRESS')
print(f"Expected: {expected}")
print(f"Match: {account.address.lower() == expected.lower()}")

# 2. Ensure .env file is loaded
import os
print(f"PRIVATE_KEY loaded: {os.getenv('PRIVATE_KEY') is not None}")
print(f"WALLET_ADDRESS loaded: {os.getenv('WALLET_ADDRESS') is not None}")

# 3. Check file permissions
# .env should be readable
ls -la .env
# Should show: -rw------- (600)
```

### Problem: Wallet Address Mismatch

**Error Message:**
```
ValueError: Wallet address does not match private key
```

**Solution:**
```python
# Derive correct wallet address from private key
from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv()
private_key = os.getenv('PRIVATE_KEY')

# Derive address
account = Account.from_key('0x' + private_key)
correct_address = account.address

print(f"Correct wallet address: {correct_address}")

# Update .env file
# WALLET_ADDRESS=0x... (use the correct_address above)
```

---

## 📊 Market Data Issues

### Problem: No Markets Found

**Error Message:**
```
No 15-minute crypto markets found
```

**Solution:**
```python
# This is expected - 15-minute markets are not currently available
# Verify by checking all markets
from py_clob_client.client import ClobClient

client = ClobClient("https://clob.polymarket.com")
markets = client.get_markets()

print(f"Total markets: {markets.get('count', 0)}")
print(f"Markets in response: {len(markets.get('data', []))}")

# Search for any crypto markets
crypto_count = 0
for market in markets.get('data', []):
    question = market.get('question', '').lower()
    if any(asset in question for asset in ['btc', 'eth', 'sol', 'xrp', 'crypto']):
        crypto_count += 1
        print(f"Found: {market.get('question')}")

print(f"Total crypto markets: {crypto_count}")

# Workaround: Use mock data for testing
from polymarket_analyzer_clob import PolymarketAnalyzer
analyzer = PolymarketAnalyzer(use_mock=True)
```

### Problem: Market Data Structure Error

**Error Message:**
```
KeyError: 'data'
TypeError: 'NoneType' object is not subscriptable
```

**Solution:**
```python
# Always check response structure
markets_response = client.get_markets()

# Safe access pattern
if markets_response and 'data' in markets_response:
    markets = markets_response['data']
else:
    print("Invalid response structure")
    markets = []

# Or use .get() with default
markets = markets_response.get('data', [])

# Validate market object
for market in markets:
    condition_id = market.get('condition_id')
    question = market.get('question', 'Unknown')
    active = market.get('active', False)
    
    if not condition_id:
        print(f"Warning: Market missing condition_id: {question}")
        continue
```

### Problem: Stale Market Data

**Error Message:**
```
Market data is outdated
```

**Solution:**
```python
# Implement cache invalidation
import time

class MarketCache:
    def __init__(self, ttl=300):  # 5 minutes
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()

# Usage
cache = MarketCache(ttl=300)

def get_markets_cached(client):
    cached = cache.get('markets')
    if cached:
        return cached
    
    markets = client.get_markets()
    cache.set('markets', markets)
    return markets
```

---

## 💰 Trading Errors

### Problem: Insufficient Balance

**Error Message:**
```
InsufficientBalanceError: Not enough USDC to place order
```

**Solution:**
```python
# 1. Check current balance
balances = client.get_balances()
usdc_balance = 0

for balance in balances.get('balances', []):
    if balance['asset'] == 'USDC':
        usdc_balance = float(balance['available'])
        print(f"Available USDC: ${usdc_balance:.2f}")

# 2. Ensure sufficient funds
required_amount = 100.0  # Your order size
if usdc_balance < required_amount:
    print(f"Need to deposit ${required_amount - usdc_balance:.2f} more")
    # Deposit USDC to your Polymarket wallet

# 3. Adjust order size
max_order_size = usdc_balance * 0.95  # Use 95% to leave buffer
print(f"Maximum order size: ${max_order_size:.2f}")
```

### Problem: Order Rejected

**Error Message:**
```
OrderRejectedError: Order does not meet minimum requirements
```

**Solution:**
```python
# Check order parameters
def validate_order(token_id, price, size):
    errors = []
    
    # Price must be between 0 and 1
    if not (0 < price < 1):
        errors.append(f"Invalid price: {price} (must be 0-1)")
    
    # Minimum order size (usually $1)
    if size < 1.0:
        errors.append(f"Order too small: ${size} (minimum $1)")
    
    # Maximum order size (check your limits)
    if size > 10000.0:
        errors.append(f"Order too large: ${size}")
    
    # Price precision (usually 2 decimals)
    if len(str(price).split('.')[-1]) > 4:
        errors.append(f"Price too precise: {price}")
    
    return errors

# Validate before placing order
errors = validate_order("123", 0.52, 100.0)
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    # Place order
    order = client.create_order(...)
```

### Problem: Market Closed

**Error Message:**
```
MarketClosedError: Market is no longer accepting orders
```

**Solution:**
```python
# Check market status before trading
def is_market_tradeable(market):
    """Check if market accepts orders"""
    checks = {
        'active': market.get('active', False),
        'not_closed': not market.get('closed', True),
        'not_archived': not market.get('archived', True),
        'accepting_orders': market.get('accepting_orders', False)
    }
    
    for check, passed in checks.items():
        if not passed:
            print(f"❌ Market failed check: {check}")
            return False
    
    return True

# Usage
market = client.get_market(condition_id="0x123...")
if is_market_tradeable(market):
    # Place order
    pass
else:
    print("Market not tradeable")
```

---

## ⚡ Performance Problems

### Problem: Slow API Responses

**Symptoms:**
- API calls taking > 10 seconds
- Bot missing trading opportunities
- Timeout errors

**Solution:**
```python
# 1. Implement connection pooling
import aiohttp
import asyncio

async def fetch_markets_async(client):
    """Async market fetching"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://clob.polymarket.com/markets",
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            return await response.json()

# 2. Use caching
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_market_cached(condition_id, cache_time):
    """Cache market data for 5 minutes"""
    return client.get_market(condition_id)

# Call with current 5-minute window
cache_key = int(time.time() / 300)
market = get_market_cached("0x123...", cache_key)

# 3. Parallel requests
import concurrent.futures

def fetch_multiple_markets(market_ids):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(client.get_market, mid)
            for mid in market_ids
        ]
        return [f.result() for f in futures]
```

### Problem: High Memory Usage

**Symptoms:**
- Bot using > 1GB RAM
- System slowdown
- Out of memory errors

**Solution:**
```python
# 1. Clear cache periodically
import gc

def cleanup_memory():
    """Force garbage collection"""
    gc.collect()
    print(f"Memory cleaned")

# Call every hour
import schedule
schedule.every(1).hours.do(cleanup_memory)

# 2. Limit market data storage
class LimitedMarketStore:
    def __init__(self, max_size=100):
        self.markets = {}
        self.max_size = max_size
    
    def add(self, market_id, market_data):
        if len(self.markets) >= self.max_size:
            # Remove oldest
            oldest = min(self.markets.keys())
            del self.markets[oldest]
        self.markets[market_id] = market_data

# 3. Use generators instead of lists
def get_markets_generator(client):
    """Yield markets one at a time"""
    response = client.get_markets()
    for market in response.get('data', []):
        yield market

# Process without loading all into memory
for market in get_markets_generator(client):
    process_market(market)
```

### Problem: Bot Crashes Frequently

**Symptoms:**
- Bot stops unexpectedly
- No error messages
- Process terminates

**Solution:**
```python
# 1. Add comprehensive error handling
import traceback
import logging

logging.basicConfig(
    filename='logs/bot_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_execute(func):
    """Wrapper for safe function execution"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            logging.error(traceback.format_exc())
            return None
    return wrapper

# 2. Implement auto-restart
import subprocess
import sys

def restart_bot():
    """Restart the bot process"""
    python = sys.executable
    subprocess.Popen([python] + sys.argv)
    sys.exit()

# 3. Monitor and restart on crash
import signal

def signal_handler(sig, frame):
    print("Bot stopping gracefully...")
    # Cleanup code here
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

## ❌ Common Error Messages

### Error: "ModuleNotFoundError: No module named 'py_clob_client'"

**Cause:** py-clob-client not installed or virtual environment not activated

**Fix:**
```bash
source venv/bin/activate
pip install git+https://github.com/Polymarket/py-clob-client.git
```

### Error: "FileNotFoundError: [Errno 2] No such file or directory: '.env'"

**Cause:** .env file missing

**Fix:**
```bash
touch .env
nano .env
# Add required variables:
# PRIVATE_KEY=your_key_here
# WALLET_ADDRESS=0xyour_address_here
```

### Error: "JSONDecodeError: Expecting value: line 1 column 1 (char 0)"

**Cause:** API returned non-JSON response (likely HTML error page)

**Fix:**
```python
import json

try:
    response = client.get_markets()
except json.JSONDecodeError as e:
    print("API returned invalid JSON")
    print("Check API status at https://status.polymarket.com")
    # Implement retry logic
```

### Error: "RuntimeError: Event loop is closed"

**Cause:** Async event loop issues

**Fix:**
```python
import asyncio

# Create new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Or use asyncio.run()
asyncio.run(your_async_function())
```

---

## ❓ FAQ

### Q: Why can't I find any 15-minute crypto markets?

**A:** 15-minute crypto markets are not currently available on Polymarket. This could be because:
- They were discontinued
- They're only available at specific times
- They require special access (market maker program)
- They haven't been launched yet

**Workaround:** Use mock data for testing or adapt bot for hourly/daily markets.

### Q: How do I know if my bot is working correctly?

**A:** Run the test suite:
```bash
python test_clob_integration.py
```

All tests should pass. Also check:
- API connection successful
- Market data fetching works
- Mock data analysis produces recommendations

### Q: Can I run the bot on a cloud server?

**A:** Yes! Deploy to:
- AWS EC2
- Google Cloud Compute
- DigitalOcean Droplet
- Heroku (with worker dyno)

Ensure:
- Python 3.11.0 installed
- .env file uploaded securely
- Firewall allows HTTPS (port 443)
- Monitoring setup

### Q: How much capital do I need to start?

**A:** Recommended:
- **Minimum:** $100 (for testing)
- **Comfortable:** $500-1000
- **Optimal:** $2000-5000

Start small and scale up as you gain confidence.

### Q: What are the trading fees?

**A:** Polymarket charges:
- **Trading Fee:** ~2% per trade
- **Gas Fees:** Minimal on Polygon (~$0.01)
- **Withdrawal Fees:** Varies by method

### Q: Is the bot profitable?

**A:** Profitability depends on:
- Market availability
- Strategy effectiveness
- Risk management
- Market conditions
- Execution speed

**No guarantees** - always trade responsibly and never risk more than you can afford to lose.

### Q: How do I update the bot?

**A:**
```bash
cd ~/CascadeProjects/polymarket-trading-bot
git pull origin main
source venv/bin/activate
pip install --upgrade git+https://github.com/Polymarket/py-clob-client.git
python test_clob_integration.py
```

### Q: Where can I get help?

**A:**
- **Documentation:** Check other files in DOCUMENTATION/
- **Polymarket Discord:** https://discord.gg/polymarket
- **GitHub Issues:** Report bugs on project repository
- **Email Support:** support@polymarket.com

---

## 🆘 Emergency Procedures

### Bot is Losing Money

1. **STOP THE BOT IMMEDIATELY**
   ```bash
   kill $(cat bot.pid)
   ```

2. **Review recent trades**
   ```bash
   tail -n 100 logs/trading_bot.log | grep "TRADE"
   ```

3. **Check positions**
   ```python
   positions = client.get_positions()
   for pos in positions.get('positions', []):
       print(f"Market: {pos['market_id']}")
       print(f"P&L: ${pos['pnl']}")
   ```

4. **Close losing positions** (if necessary)

5. **Analyze what went wrong**

6. **Fix the issue before restarting**

### Private Key Compromised

1. **STOP THE BOT**
   ```bash
   kill $(cat bot.pid)
   ```

2. **Create new wallet**

3. **Transfer funds to new wallet**

4. **Update .env with new private key**

5. **Rotate all API keys**

6. **Review security practices**

### System Crash

1. **Check if bot is running**
   ```bash
   ps aux | grep python
   ```

2. **Check logs for errors**
   ```bash
   tail -n 50 logs/bot_errors.log
   ```

3. **Restart bot**
   ```bash
   cd ~/CascadeProjects/polymarket-trading-bot
   source venv/bin/activate
   nohup python trading_bot.py > logs/bot_output.log 2>&1 &
   echo $! > bot.pid
   ```

4. **Monitor for stability**
   ```bash
   tail -f logs/trading_bot.log
   ```

---

## 📞 Getting Additional Help

### Before Asking for Help

Gather this information:
- Python version: `python --version`
- OS version: `uname -a` (Linux/Mac) or `ver` (Windows)
- Error message (full traceback)
- Steps to reproduce
- What you've tried already

### Where to Ask

1. **Project Documentation** (check all files first)
2. **Polymarket Discord** (community support)
3. **GitHub Issues** (bug reports)
4. **Stack Overflow** (technical questions)

### Include in Your Question

- Clear description of the problem
- Error messages (full text)
- Code snippets (relevant parts)
- What you've tried
- Expected vs actual behavior

---

**End of Troubleshooting Guide**
