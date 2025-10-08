# 🚀 Dual DEX Trading Bot

A sophisticated automated trading bot that implements a dual DEX hedging strategy using both **Lighter Protocol** and **Pacifica Finance**.

## 🎯 Key Features

- **🔄 Dual DEX Strategy**: Places opposite orders on Lighter and Pacifica DEXes
- **✅ Position Verification**: Double-checks all position operations before proceeding
- **🎲 Random Order Assignment**: Randomly assigns buy/sell orders to each DEX
- **⏱️ Dynamic Hold Times**: Configurable position hold periods
- **📊 Comprehensive Logging**: Detailed trade tracking and error handling
- **🔒 Proxy Support**: Secure connection routing for both DEXes
- **💰 Risk Management**: Percentage-based position sizing

## 🔄 Trading Workflow

1. **🔍 Startup Check**: Verify no open positions exist on either DEX
2. **🧹 Position Cleanup**: Close any existing positions with verification
3. **📈 Order Placement**: Place opposite orders (buy on one DEX, sell on other)
4. **⏳ Position Hold**: Wait for configured time period
5. **🔒 Position Close**: Close positions on both DEXes with verification
6. **🔄 Cycle Repeat**: Return to step 3

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Valid accounts on both Lighter Protocol and Pacifica Finance
- Proxy server (mandatory for both DEXes)

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd dual-dex-trading-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your actual credentials
   ```

4. **Required environment variables:**
   ```bash
   # Lighter Protocol
   LIGHTER_API_KEY_PRIVATE_KEY=0x...
   LIGHTER_ACCOUNT_INDEX=1
   LIGHTER_API_KEY_INDEX=0
   
   # Pacifica Finance
   PACIFICA_PRIVATE_KEY=your_base58_private_key
   
   # Trading Configuration
   ACCOUNT_BALANCE=500.0
   MIN_POSITION_PERCENT=50.0
   MAX_POSITION_PERCENT=80.0
   POSITION_HOLD_MINUTES=5
   
   # Proxy (MANDATORY)
   USE_PROXY=true
   PROXY_URL=http://username:password@proxy.example.com:8080
   
   # Trading Pairs
   ALLOWED_TRADING_PAIRS=BTC,ETH,HYPE,SOL,BNB
   ```

## 🚀 Usage

### Process Management

The bot includes a comprehensive process manager:

```bash
# Start the bot
python3 start_bot.py start

# Check status
python3 start_bot.py status

# View logs in real-time
python3 start_bot.py logs

# Stop the bot
python3 start_bot.py stop

# Restart the bot
python3 start_bot.py restart
```

### Direct Execution

You can also run the bot directly:

```bash
python3 dual_dex_bot.py
```

## ⚙️ Configuration

### Trading Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ACCOUNT_BALANCE` | Account balance for percentage calculations (USD) | 500.0 |
| `MIN_POSITION_PERCENT` | Minimum position size as % of balance | 50.0 |
| `MAX_POSITION_PERCENT` | Maximum position size as % of balance | 80.0 |
| `POSITION_HOLD_MINUTES` | How long to hold positions | 5 |
| `MIN_WAIT_BETWEEN_CYCLES` | Minimum wait between cycles (seconds) | 30 |
| `MAX_WAIT_BETWEEN_CYCLES` | Maximum wait between cycles (seconds) | 120 |

### Leverage Settings

Configure leverage per trading pair:

```bash
LEVERAGE_BTC=5.0
LEVERAGE_ETH=5.0
LEVERAGE_HYPE=5.0
LEVERAGE_SOL=5.0
LEVERAGE_BNB=5.0
```

### Trading Pairs

Specify which pairs to trade:

```bash
ALLOWED_TRADING_PAIRS=BTC,ETH,HYPE,SOL,BNB
```

## 📊 Monitoring

### Logs

The bot creates detailed logs in `dual_dex_bot.log`:

- **🔍 Position Detection**: Startup position cleanup
- **📈 Order Placement**: Order details and confirmations
- **⏳ Position Management**: Hold times and status updates
- **🔒 Position Closing**: Close operations and verification
- **📊 Statistics**: Trading performance metrics

### Statistics

The bot tracks comprehensive statistics:

- **Cycle Statistics**: Total cycles, success rate, runtime
- **Lighter Statistics**: Trades, success rate, positions
- **Pacifica Statistics**: Trades, success rate, positions

## 🔒 Security

### Proxy Requirements

**Proxy usage is mandatory** for both DEXes. Configure your proxy:

```bash
USE_PROXY=true
PROXY_URL=http://username:password@your-proxy.com:8080
```

### Credential Safety

- Never commit `.env` files to version control
- Use strong, unique API keys
- Regularly rotate credentials
- Monitor account activity

## ⚠️ Risk Disclaimer

**IMPORTANT**: This bot is for educational and testing purposes only.

- **High Risk**: Automated trading involves significant financial risk
- **No Guarantees**: Past performance does not guarantee future results
- **Use at Your Own Risk**: Ensure you understand the implications
- **Test First**: Always test with small amounts initially
- **Monitor Closely**: Never leave the bot unattended for extended periods

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify proxy configuration
   - Check API credentials
   - Ensure network connectivity

2. **Position Issues**
   - Check account balances
   - Verify trading permissions
   - Review position limits

3. **Order Failures**
   - Check market status
   - Verify position sizes
   - Review slippage settings

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

## 📈 Performance Tips

1. **Optimal Settings**
   - Start with conservative position sizes
   - Use shorter hold times for testing
   - Monitor performance closely

2. **Risk Management**
   - Set appropriate leverage limits
   - Use stop-loss mechanisms
   - Diversify across multiple pairs

3. **Monitoring**
   - Check logs regularly
   - Monitor account balances
   - Track performance metrics

## 🤝 Contributing

This bot combines the best practices from both individual DEX implementations:

- **Lighter Protocol**: Advanced position management and verification
- **Pacifica Finance**: Robust error handling and retry mechanisms

## 📄 License

This project is for educational purposes only. Use at your own risk.

---

**⚠️ Remember**: Always test thoroughly with small amounts before using real funds. Automated trading carries significant financial risk.
