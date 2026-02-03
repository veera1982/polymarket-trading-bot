# Polymarket Trading Bot

A sophisticated automated trading bot for Polymarket that specializes in 15-minute Bitcoin (BTC) markets. The bot uses advanced algorithms to detect market direction and execute trades based on probability thresholds.

## Features

### 🎯 Core Trading Functionality
- **Market Detection**: Automatically finds active 15-minute BTC markets on Polymarket
- **Direction Analysis**: Watches markets for 5 minutes to determine price direction (up/down)
- **Smart Trading**: Executes trades only when probability ≥ 70% and direction is clear
- **Risk Management**: Built-in trade limits ($0.8 per trade, $5 daily maximum)

### 🔄 Self-Healing & Reliability
- **Automatic Reconnection**: Restores connection to Polymarket API if lost
- **Error Recovery**: Handles API failures and restarts automatically
- **Health Monitoring**: Continuous health checks with automatic healing
- **Graceful Shutdown**: Clean shutdown on signals (SIGINT, SIGTERM)

### 📊 Market Analysis
- **Trend Detection**: Uses linear regression to identify price trends
- **Volatility Analysis**: Calculates market volatility for risk assessment
- **Momentum Indicators**: Measures price momentum for better predictions
- **Probability Filtering**: Only trades markets with ≥70% probability

### 🧪 Testing & Quality
- **Comprehensive Tests**: Unit, integration, and end-to-end tests
- **Test Reports**: HTML and XML coverage reports
- **Mock Testing**: Full API mocking for reliable testing
- **Ubuntu Compatible**: Tested on Ubuntu and macOS

## Installation

### Prerequisites
- Python 3.8+
- Node.js (for some dependencies)
- Git

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd polymarket-trading-bot
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Verify installation**
```bash
python -m pytest tests/ -v
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Polymarket API Configuration
POLYMARKET_API_URL=https://gamma-api.polymarket.com
POLYMARKET_GRAPHQL_URL=https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic

# Wallet Configuration (Required for live trading)
PRIVATE_KEY=your_private_key_here
WALLET_ADDRESS=your_wallet_address_here

# Trading Configuration
MAX_TRADE_AMOUNT=5.0
DEFAULT_TRADE_AMOUNT=0.8
PROBABILITY_THRESHOLD=0.7
WATCH_DURATION_SECONDS=300

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=trading_bot.log

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### Trading Parameters

- **MAX_TRADE_AMOUNT**: Maximum total daily trading amount ($5.00 default)
- **DEFAULT_TRADE_AMOUNT**: Default amount per trade ($0.80 default)
- **PROBABILITY_THRESHOLD**: Minimum probability to execute trade (70% default)
- **WATCH_DURATION_SECONDS**: Time to watch market before trading (300 seconds = 5 minutes)

## Usage

### Running the Bot

#### Single Trading Cycle (Testing)
```bash
python trading_bot.py --mode single
```

#### Continuous Trading (Production)
```bash
python trading_bot.py --mode continuous
```

#### Test Mode (Simulated Trades)
```bash
python trading_bot.py --mode single --test
```

### Running Tests

#### All Tests
```bash
python run_tests.py
```

#### Unit Tests Only
```bash
python run_tests.py --type unit
```

#### Integration Tests Only
```bash
python run_tests.py --type integration
```

#### Without Coverage
```bash
python run_tests.py --no-coverage
```

### Test Reports

After running tests, you can find detailed reports in:
- `test_reports/coverage/index.html` - Coverage report
- `test_reports/test_report_*.html` - Test execution report
- `test_reports/summary.md` - Summary report

## Architecture

### Core Components

1. **PolymarketClient** (`polymarket_client.py`)
   - API communication with Polymarket
   - Self-healing connection management
   - Market and token data fetching

2. **MarketAnalyzer** (`market_analyzer.py`)
   - Market direction detection
   - Trend and volatility analysis
   - Signal generation

3. **Trader** (`trader.py`)
   - Trade execution logic
   - Risk management
   - Blockchain interaction

4. **TradingBot** (`trading_bot.py`)
   - Main orchestration
   - Health monitoring
   - Error recovery

### Data Flow

```
1. Market Discovery → 2. Direction Analysis → 3. Signal Generation → 4. Trade Execution
     ↓                      ↓                      ↓                      ↓
Polymarket API        5-min Watching        Probability Filter    Risk Management
```

## Trading Strategy

### Market Selection
- Filters for active 15-minute BTC markets
- Scores markets by liquidity and volume
- Selects highest-scoring market

### Direction Detection
- Monitors price changes every 10 seconds for 5 minutes
- Uses linear regression to identify trends
- Calculates volatility and momentum indicators

### Trade Execution
- Only trades when:
  - Direction is clear (up/down, not neutral)
  - Probability ≥ 70%
  - Daily trade limit not exceeded
- Executes at current market price
- Records trade details for analysis

## Risk Management

### Built-in Protections
- **Daily Limits**: Maximum $5.00 total per day
- **Per-Trade Limits**: Maximum $0.80 per trade
- **Probability Threshold**: Only trades ≥70% probability
- **Direction Confirmation**: Requires clear directional signal
- **Connection Healing**: Automatic recovery from API failures

### Safety Features
- **Simulation Mode**: Test without real money
- **Comprehensive Logging**: All actions logged
- **Error Handling**: Graceful failure recovery
- **Health Monitoring**: Continuous system health checks

## Monitoring & Logging

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Log Files
- `trading_bot.log`: Main application log
- Console output: Real-time colored logging

### Health Checks
- API connectivity verification
- System health monitoring
- Automatic error recovery

## Development

### Project Structure
```
polymarket-trading-bot/
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── polymarket_client.py   # API client
├── market_analyzer.py     # Market analysis
├── trader.py              # Trading logic
├── trading_bot.py         # Main bot
├── requirements.txt       # Dependencies
├── pytest.ini            # Test configuration
├── run_tests.py          # Test runner
├── tests/                # Test suite
│   ├── test_polymarket_client.py
│   ├── test_market_analyzer.py
│   ├── test_trader.py
│   └── test_integration.py
├── test_reports/         # Generated test reports
└── README.md            # This file
```

### Adding Features

1. **New Analysis Methods**: Add to `MarketAnalyzer`
2. **New Trading Strategies**: Add to `Trader`
3. **New API Endpoints**: Add to `PolymarketClient`
4. **New Tests**: Add to appropriate test file

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Document all public methods
- Write comprehensive tests

## Troubleshooting

### Common Issues

#### Connection Problems
- Check internet connectivity
- Verify Polymarket API status
- Check firewall settings
- Review logs for error details

#### Trading Issues
- Verify wallet configuration
- Check MATIC balance for gas fees
- Ensure market is active
- Review probability thresholds

#### Test Failures
- Update dependencies: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify test environment setup

### Getting Help

1. **Check Logs**: Review `trading_bot.log` for errors
2. **Run Tests**: `python run_tests.py` to verify functionality
3. **Health Check**: Monitor API connectivity
4. **Configuration**: Verify `.env` settings

## Security

### Private Key Management
- Never commit private keys to version control
- Use environment variables for sensitive data
- Consider using a hardware wallet for production
- Regularly rotate private keys

### API Security
- Rate limiting implemented
- Connection timeouts configured
- Error handling prevents data leakage
- Secure HTTP headers used

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

**⚠️ IMPORTANT DISCLAIMER**

This trading bot is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. The authors are not responsible for any financial losses incurred while using this software.

- **Never trade more than you can afford to lose**
- **Start with small amounts in test mode**
- **Understand the risks before trading**
- **Comply with local regulations**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and error messages

---

**Happy Trading! 🚀**
