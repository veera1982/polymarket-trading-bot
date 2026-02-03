# Polymarket Trading Bot - Deployment Guide

**Last Updated:** February 3, 2026  
**Python Version Required:** 3.9.10+ (3.11.0 recommended)  
**Status:** Ready for deployment when markets become available

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### System Requirements
- **Operating System:** macOS, Linux, or Windows
- **Python:** 3.9.10 or higher (3.11.0 recommended)
- **Memory:** Minimum 2GB RAM
- **Storage:** 500MB free space
- **Internet:** Stable connection required

### Required Accounts
- **Polymarket Account:** Create at https://polymarket.com
- **Ethereum Wallet:** MetaMask or similar
- **USDCe Funding:** For trading (Polygon network)

### Knowledge Requirements
- Basic command line usage
- Understanding of prediction markets
- Familiarity with cryptocurrency wallets
- Risk management principles

---

## 🌍 Environment Setup

### Step 1: Install pyenv (Python Version Manager)

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install pyenv
brew update
brew install pyenv

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

**Linux:**
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

### Step 2: Install Python 3.11.0

```bash
# Install Python 3.11.0
pyenv install 3.11.0

# Verify installation
pyenv versions
```

### Step 3: Clone or Navigate to Project

```bash
# If cloning from repository
git clone <your-repo-url> polymarket-trading-bot
cd polymarket-trading-bot

# If already exists
cd ~/CascadeProjects/polymarket-trading-bot
```

---

## 📦 Installation Steps

### Step 1: Set Python Version

```bash
# Set local Python version for project
pyenv local 3.11.0

# Verify
python --version
# Should output: Python 3.11.0
```

### Step 2: Create Virtual Environment

```bash
# Remove old virtual environment if exists
rm -rf venv

# Create new virtual environment with Python 3.11.0
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install py-clob-client from GitHub
pip install git+https://github.com/Polymarket/py-clob-client.git

# Install additional dependencies
pip install eth-account web3 python-dotenv aiohttp

# Verify installation
python -c "from py_clob_client.client import ClobClient; print('✅ py-clob-client installed successfully')"
```

### Step 4: Verify Installation

```bash
# Check all required packages
pip list | grep -E "py-clob-client|eth-account|web3|python-dotenv|aiohttp"

# Expected output:
# aiohttp                  3.x.x
# eth-account             0.x.x
# py-clob-client          0.34.5
# python-dotenv           1.x.x
# web3                    6.x.x
```

---

## ⚙️ Configuration

### Step 1: Create Environment File

```bash
# Create .env file
touch .env

# Open in text editor
nano .env
# OR
vim .env
# OR
code .env  # VS Code
```

### Step 2: Add Configuration Variables

Add the following to `.env`:

```bash
# Polymarket Configuration
POLYMARKET_API_URL=https://clob.polymarket.com
POLYMARKET_GRAPHQL_URL=https://gamma-api.polymarket.com/query

# Wallet Configuration
PRIVATE_KEY=your_private_key_here_without_0x_prefix
WALLET_ADDRESS=your_wallet_address_here_with_0x_prefix

# Trading Configuration
MAX_POSITION_SIZE=100.0
MIN_PROFIT_THRESHOLD=0.02
RISK_PERCENTAGE=0.05

# Bot Configuration
CHECK_INTERVAL=60
LOG_LEVEL=INFO
```

### Step 3: Secure Your Private Key

**⚠️ CRITICAL SECURITY STEPS:**

```bash
# Set proper permissions on .env file
chmod 600 .env

# Add .env to .gitignore
echo ".env" >> .gitignore

# Verify .env is not tracked by git
git status

# NEVER commit .env to version control
```

### Step 4: Export Wallet Private Key

**From MetaMask:**
1. Open MetaMask extension
2. Click three dots → Account Details
3. Click "Export Private Key"
4. Enter password
5. Copy private key (remove "0x" prefix)
6. Paste into .env file

**Security Best Practices:**
- Use a dedicated trading wallet
- Never share your private key
- Keep minimal funds in trading wallet
- Use hardware wallet for large amounts
- Regularly rotate keys

---

## 🧪 Testing

### Step 1: Test API Connection

```bash
# Activate virtual environment
source venv/bin/activate

# Test live API connection
python validate_markets.py
```

**Expected Output:**
```
Initializing CLOB Client...
Fetching all markets...
Total markets: 1000+
Searching for 15-minute crypto markets...
Total 15-minute crypto markets found: 0
```

### Step 2: Test with Mock Data

```bash
# Run integration tests
python test_clob_integration.py
```

**Expected Output:**
```
Testing mock market data...
✅ Mock data loaded successfully
✅ 4 markets available

Testing market analyzer...
✅ Analyzer initialized
✅ Market data fetched

Testing trade recommendations...
✅ Recommendations generated
✅ Risk checks passed

All tests passed! ✅
```

### Step 3: Search for Available Markets

```bash
# Search for crypto markets
python search_crypto_markets.py
```

**Expected Output:**
```
Initializing CLOB Client...
Fetching all markets...
Total markets: 1000
Searching for ANY crypto-related markets...
Total crypto markets found (first 100): 0
```

### Step 4: Test Bot Components

```bash
# Test market analyzer
python -c "
from polymarket_analyzer_clob import PolymarketAnalyzer
analyzer = PolymarketAnalyzer(use_mock=True)
print('✅ Analyzer working')
"

# Test CLOB client
python -c "
from py_clob_client.client import ClobClient
client = ClobClient('https://clob.polymarket.com')
print('✅ CLOB client working')
"
```

---

## 🚀 Deployment

### Current Status: BLOCKED ⚠️

**Reason:** No 15-minute crypto markets currently available on Polymarket

### When Markets Become Available

#### Step 1: Validate Market Availability

```bash
# Run validation script
python validate_markets.py

# Look for output showing markets found
# Example: "Total 15-minute crypto markets found: 4"
```

#### Step 2: Extract Market IDs

```bash
# Run search script to get market details
python search_crypto_markets.py > market_ids.txt

# Review market IDs
cat market_ids.txt
```

#### Step 3: Update Configuration

Edit your bot configuration to use discovered market IDs:

```python
# In your bot configuration
MARKET_IDS = {
    'BTC': 'extracted_btc_market_id',
    'ETH': 'extracted_eth_market_id',
    'SOL': 'extracted_sol_market_id',
    'XRP': 'extracted_xrp_market_id'
}
```

#### Step 4: Execute Test Trade

```bash
# Run bot in test mode (small position)
python trading_bot.py --test-mode --max-position=10
```

#### Step 5: Monitor Initial Performance

```bash
# Watch logs in real-time
tail -f logs/trading_bot.log

# Check for:
# - Successful market data fetching
# - Trade signal generation
# - Order placement
# - Position management
```

#### Step 6: Deploy for Production

```bash
# Run bot in production mode
nohup python trading_bot.py > logs/bot_output.log 2>&1 &

# Save process ID
echo $! > bot.pid

# Verify bot is running
ps -p $(cat bot.pid)
```

---

## 📊 Monitoring

### Real-Time Monitoring

```bash
# Monitor logs
tail -f logs/trading_bot.log

# Monitor system resources
top -p $(cat bot.pid)

# Monitor network connections
netstat -an | grep clob.polymarket.com
```

### Daily Checks

```bash
# Check bot status
ps -p $(cat bot.pid) && echo "✅ Bot running" || echo "❌ Bot stopped"

# Check recent trades
tail -n 50 logs/trading_bot.log | grep "TRADE"

# Check error rate
grep "ERROR" logs/trading_bot.log | wc -l

# Check market availability
python validate_markets.py
```

### Performance Metrics

Monitor these key metrics:
- **Uptime:** Bot should run 24/7
- **API Response Time:** < 2 seconds
- **Trade Execution Time:** < 5 seconds
- **Error Rate:** < 1% of requests
- **Profit/Loss:** Track daily P&L

---

## 🔄 Maintenance

### Daily Tasks
- Check bot status
- Review trade logs
- Monitor market availability
- Verify wallet balance

### Weekly Tasks
- Analyze performance metrics
- Review and adjust strategies
- Update market configurations
- Backup logs and data

### Monthly Tasks
- Review and optimize code
- Update dependencies
- Security audit
- Performance tuning

---

## 🛑 Stopping the Bot

```bash
# Stop bot gracefully
kill $(cat bot.pid)

# Force stop if needed
kill -9 $(cat bot.pid)

# Verify stopped
ps -p $(cat bot.pid) || echo "Bot stopped"

# Deactivate virtual environment
deactivate
```

---

## 🔄 Updating the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest code
git pull origin main

# Update dependencies
pip install --upgrade git+https://github.com/Polymarket/py-clob-client.git

# Run tests
python test_clob_integration.py

# Restart bot
kill $(cat bot.pid)
nohup python trading_bot.py > logs/bot_output.log 2>&1 &
echo $! > bot.pid
```

---

## 📱 Automated Monitoring Setup

### Create Monitoring Script

```bash
# Create monitor.sh
cat > monitor.sh << 'EOF'
#!/bin/bash

# Check if bot is running
if ! ps -p $(cat bot.pid) > /dev/null 2>&1; then
    echo "❌ Bot stopped at $(date)" >> logs/monitor.log
    # Restart bot
    cd ~/CascadeProjects/polymarket-trading-bot
    source venv/bin/activate
    nohup python trading_bot.py > logs/bot_output.log 2>&1 &
    echo $! > bot.pid
    echo "✅ Bot restarted at $(date)" >> logs/monitor.log
fi

# Check market availability
python validate_markets.py >> logs/market_check.log
EOF

# Make executable
chmod +x monitor.sh
```

### Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add monitoring job (runs every 5 minutes)
*/5 * * * * /path/to/polymarket-trading-bot/monitor.sh
```

---

## 🎯 Quick Start Checklist

- [ ] Install pyenv
- [ ] Install Python 3.11.0
- [ ] Create virtual environment
- [ ] Install py-clob-client
- [ ] Create .env file
- [ ] Add private key and wallet address
- [ ] Secure .env file (chmod 600)
- [ ] Test API connection
- [ ] Run integration tests
- [ ] Check market availability
- [ ] Wait for 15-minute markets to appear
- [ ] Extract market IDs when available
- [ ] Execute test trade
- [ ] Deploy for production
- [ ] Setup monitoring
- [ ] Configure automated checks

---

## 📞 Support

### Common Issues
See [05_TROUBLESHOOTING.md](05_TROUBLESHOOTING.md) for detailed solutions

### Resources
- Polymarket Docs: https://docs.polymarket.com
- py-clob-client: https://github.com/Polymarket/py-clob-client
- Project Documentation: ~/CascadeProjects/polymarket-trading-bot/DOCUMENTATION

---

**End of Deployment Guide**
