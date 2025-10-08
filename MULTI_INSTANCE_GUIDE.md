# 🚀 Multi-Instance Trading Bot Guide

This guide explains how to run multiple instances of the same bot with different accounts.

## 📋 Overview

You can run multiple independent bot instances, each with:
- ✅ Separate Lighter + Pacifica account credentials
- ✅ Separate log files
- ✅ Separate PID files (for independent process management)
- ✅ Same codebase (updates apply to all instances)
- ✅ Separate proxy settings (if needed)

## 🔧 Setup Instructions

### Step 1: Create Multiple Environment Files

Create separate `.env` files for each account pair:

```bash
# Copy your existing .env to account-specific files
cp .env .env.account1
cp .env .env.account2
cp .env .env.account3
```

### Step 2: Configure Each Environment File

Edit each `.env.accountX` file with different credentials:

**`.env.account1`:**
```bash
# Lighter Protocol Credentials (Account 1)
LIGHTER_API_KEY_PRIVATE_KEY=your_lighter_key_1
LIGHTER_ACCOUNT_INDEX=0
LIGHTER_API_KEY_INDEX=0

# Pacifica Finance Credentials (Account 1)
PACIFICA_PRIVATE_KEY=your_pacifica_key_1

# Proxy (if needed)
LIGHTER_PROXY_URL=http://proxy1:port
PACIFICA_PROXY_URL=http://proxy1:port

# Trading settings (can be same or different per account)
ACCOUNT_BALANCE=2000.0
MIN_POSITION_PERCENT=50.0
MAX_POSITION_PERCENT=80.0
```

**`.env.account2`:**
```bash
# Lighter Protocol Credentials (Account 2)
LIGHTER_API_KEY_PRIVATE_KEY=your_lighter_key_2
LIGHTER_ACCOUNT_INDEX=0
LIGHTER_API_KEY_INDEX=0

# Pacifica Finance Credentials (Account 2)
PACIFICA_PRIVATE_KEY=your_pacifica_key_2

# Proxy (if needed - can be different)
LIGHTER_PROXY_URL=http://proxy2:port
PACIFICA_PROXY_URL=http://proxy2:port

# Trading settings
ACCOUNT_BALANCE=1500.0
MIN_POSITION_PERCENT=50.0
MAX_POSITION_PERCENT=80.0
```

### Step 3: Start Multiple Instances

Start each instance with its own env file:

```bash
# Start instance 1 (account1)
python3 start_bot.py start --env .env.account1

# Start instance 2 (account2)
python3 start_bot.py start --env .env.account2

# Start instance 3 (account3)
python3 start_bot.py start --env .env.account3
```

Each instance will:
- Run independently in the background
- Have its own PID file: `.dual_dex_bot_env_account1.pid`
- Have its own log file: `dual_dex_bot_env_account1.log`

## 📊 Managing Multiple Instances

### Check Status

```bash
# Check status of specific instance
python3 start_bot.py status --env .env.account1
python3 start_bot.py status --env .env.account2

# Or check default instance
python3 start_bot.py status
```

### View Logs

```bash
# Follow logs for account1
python3 start_bot.py logs --env .env.account1

# Follow logs for account2
python3 start_bot.py logs --env .env.account2

# View recent logs (don't follow)
python3 start_bot.py logs --env .env.account1 --no-follow
```

### Stop Instances

```bash
# Stop specific instance
python3 start_bot.py stop --env .env.account1
python3 start_bot.py stop --env .env.account2

# Stop all instances
python3 start_bot.py stop --env .env.account1
python3 start_bot.py stop --env .env.account2
python3 start_bot.py stop --env .env.account3
```

### Restart Instances

```bash
# Restart specific instance
python3 start_bot.py restart --env .env.account1

# Restart all instances (one by one)
python3 start_bot.py restart --env .env.account1
python3 start_bot.py restart --env .env.account2
python3 start_bot.py restart --env .env.account3
```

## 📁 File Structure

After starting multiple instances, your directory will look like:

```
dual-dex-trading-bot/
├── .env                              # Default env (optional)
├── .env.account1                     # Account 1 credentials
├── .env.account2                     # Account 2 credentials
├── .env.account3                     # Account 3 credentials
│
├── .dual_dex_bot.pid                 # Default instance PID
├── .dual_dex_bot_env_account1.pid    # Account 1 PID
├── .dual_dex_bot_env_account2.pid    # Account 2 PID
├── .dual_dex_bot_env_account3.pid    # Account 3 PID
│
├── dual_dex_bot.log                  # Default instance logs
├── dual_dex_bot_env_account1.log     # Account 1 logs
├── dual_dex_bot_env_account2.log     # Account 2 logs
├── dual_dex_bot_env_account3.log     # Account 3 logs
│
├── dual_dex_bot.py                   # Main bot (shared)
├── config.py                         # Config loader (shared)
├── start_bot.py                      # Process manager (shared)
└── ...
```

## 🔒 Security Notes

1. **All `.env.*` files are automatically ignored by Git**
   - The `.gitignore` includes `.env.*` pattern
   - Your credentials are safe from being committed

2. **Each instance is isolated**
   - Separate processes
   - Separate log files
   - No conflicts between instances

3. **Same codebase**
   - Update the code once
   - All instances use the updated code on restart

## 🎯 Example: Running 3 Accounts

```bash
# 1. Create environment files
cp .env .env.account1
cp .env .env.account2
cp .env .env.account3

# 2. Edit each file with different credentials
nano .env.account1  # Set account 1 keys
nano .env.account2  # Set account 2 keys
nano .env.account3  # Set account 3 keys

# 3. Start all instances
python3 start_bot.py start --env .env.account1
python3 start_bot.py start --env .env.account2
python3 start_bot.py start --env .env.account3

# 4. Check all are running
python3 start_bot.py status --env .env.account1
python3 start_bot.py status --env .env.account2
python3 start_bot.py status --env .env.account3

# 5. Monitor logs in separate terminals
# Terminal 1:
python3 start_bot.py logs --env .env.account1

# Terminal 2:
python3 start_bot.py logs --env .env.account2

# Terminal 3:
python3 start_bot.py logs --env .env.account3
```

## ⚙️ Advanced Usage

### Different Trading Strategies Per Account

Each `.env` file can have different trading parameters:

```bash
# .env.account1 - Aggressive
ACCOUNT_BALANCE=2000.0
MIN_POSITION_PERCENT=70.0
MAX_POSITION_PERCENT=90.0
MIN_POSITION_HOLD_MINUTES=1
MAX_POSITION_HOLD_MINUTES=3

# .env.account2 - Conservative
ACCOUNT_BALANCE=1000.0
MIN_POSITION_PERCENT=30.0
MAX_POSITION_PERCENT=50.0
MIN_POSITION_HOLD_MINUTES=5
MAX_POSITION_HOLD_MINUTES=10
```

### Different Proxies Per Account

```bash
# .env.account1
LIGHTER_PROXY_URL=http://proxy1:port
PACIFICA_PROXY_URL=http://proxy1:port

# .env.account2
LIGHTER_PROXY_URL=http://proxy2:port
PACIFICA_PROXY_URL=http://proxy2:port
```

### Monitoring All Instances

Create a simple monitoring script:

```bash
#!/bin/bash
# check_all_bots.sh

echo "=== Bot Status ==="
for env_file in .env.account*; do
    echo "Checking $env_file..."
    python3 start_bot.py status --env $env_file
    echo ""
done
```

## 🚨 Troubleshooting

### Instance Won't Start
1. Check the env file exists: `ls -la .env.account1`
2. Check credentials are correct in the env file
3. Check logs: `python3 start_bot.py logs --env .env.account1 --no-follow`

### Wrong Account Being Used
1. Stop the instance: `python3 start_bot.py stop --env .env.account1`
2. Clear cache: `rm -rf __pycache__`
3. Start again: `python3 start_bot.py start --env .env.account1`

### Can't Find Instance
- Make sure you're using the same `--env` argument you used to start it
- Check PID files: `ls -la .dual_dex_bot*.pid`

## 📞 Support

If you encounter issues:
1. Check the specific instance logs
2. Verify credentials in the env file
3. Ensure no port conflicts or resource limits
4. Try restarting the instance

---

**Happy Trading! 🚀**

