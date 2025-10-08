# =============================================================================
# DUAL DEX TRADING BOT CONFIGURATION
# =============================================================================
# Merged configuration for both Lighter Protocol and Pacifica Finance

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from custom env file (if specified) or default .env
env_file = os.getenv('DUAL_DEX_ENV_FILE', '.env')
load_dotenv(dotenv_path=env_file)

def get_env_str(key: str, default: str = "") -> str:
    """Get string environment variable"""
    return os.getenv(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """Get list environment variable (comma-separated)"""
    if default is None:
        default = []
    value = os.getenv(key, '')
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]

# =============================================================================
# LIGHTER PROTOCOL CONFIGURATION
# =============================================================================
LIGHTER_MAINNET_URL = "https://mainnet.zklighter.elliot.ai"
LIGHTER_WS_URL = "wss://ws.lighter.xyz"

# Lighter API credentials
LIGHTER_API_KEY_PRIVATE_KEY = get_env_str("LIGHTER_API_KEY_PRIVATE_KEY")
LIGHTER_ACCOUNT_INDEX = get_env_int("LIGHTER_ACCOUNT_INDEX", 0)
LIGHTER_API_KEY_INDEX = get_env_int("LIGHTER_API_KEY_INDEX", 0)

# =============================================================================
# PACIFICA FINANCE CONFIGURATION
# =============================================================================
PACIFICA_MAINNET_URL = "https://api.pacifica.fi/api/v1"
PACIFICA_WS_URL = "wss://ws.pacifica.fi/ws"

# Pacifica private key (Solana wallet)
PACIFICA_PRIVATE_KEY = get_env_str("PACIFICA_PRIVATE_KEY")

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
# Account balance for percentage calculations
ACCOUNT_BALANCE = get_env_float("ACCOUNT_BALANCE", 500.0)

# Position sizing as percentage of account balance
MIN_POSITION_PERCENT = get_env_float("MIN_POSITION_PERCENT", 50.0)
MAX_POSITION_PERCENT = get_env_float("MAX_POSITION_PERCENT", 80.0)

# Position hold time in minutes (dynamic range)
MIN_POSITION_HOLD_MINUTES = get_env_int("MIN_POSITION_HOLD_MINUTES", 2)
MAX_POSITION_HOLD_MINUTES = get_env_int("MAX_POSITION_HOLD_MINUTES", 5)
# Legacy support - if POSITION_HOLD_MINUTES is set, use it as both min and max
POSITION_HOLD_MINUTES = get_env_int("POSITION_HOLD_MINUTES", None)
if POSITION_HOLD_MINUTES is not None:
    MIN_POSITION_HOLD_MINUTES = POSITION_HOLD_MINUTES
    MAX_POSITION_HOLD_MINUTES = POSITION_HOLD_MINUTES

# Wait time between trading cycles (seconds)
MIN_WAIT_BETWEEN_CYCLES = get_env_int("MIN_WAIT_BETWEEN_CYCLES", 30)
MAX_WAIT_BETWEEN_CYCLES = get_env_int("MAX_WAIT_BETWEEN_CYCLES", 120)

# Trading intervals (seconds)
MIN_TRADE_INTERVAL = get_env_int("MIN_TRADE_INTERVAL", 30)
MAX_TRADE_INTERVAL = get_env_int("MAX_TRADE_INTERVAL", 300)

# Risk management
MAX_DAILY_TRADES = get_env_int("MAX_DAILY_TRADES", 50)
ENABLE_RISK_LIMITS = get_env_bool("ENABLE_RISK_LIMITS", True)

# =============================================================================
# LEVERAGE CONFIGURATION
# =============================================================================
# Manual leverage settings per pair
MANUAL_LEVERAGE: Dict[str, float] = {
    "BTC": get_env_float("LEVERAGE_BTC", 5.0),
    "ETH": get_env_float("LEVERAGE_ETH", 5.0),
    "HYPE": get_env_float("LEVERAGE_HYPE", 5.0),
    "SOL": get_env_float("LEVERAGE_SOL", 5.0),
    "BNB": get_env_float("LEVERAGE_BNB", 5.0),
}

# Margin mode (0 = cross, 1 = isolated)
MARGIN_MODE = get_env_int("MARGIN_MODE", 0)

# =============================================================================
# PROXY CONFIGURATION (MANDATORY)
# =============================================================================
# Proxy is REQUIRED for this bot - always set to true
USE_PROXY = get_env_bool("USE_PROXY", True)

# REQUIRED: Proxy URL with authentication
PROXY_URL = get_env_str("PROXY_URL")

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL = get_env_str("LOG_LEVEL", "INFO")
LOG_TO_FILE = get_env_bool("LOG_TO_FILE", True)
LOG_FILE = get_env_str("LOG_FILE", "dual_dex_bot.log")

# =============================================================================
# MARKET CONFIGURATION
# =============================================================================
# Trading pairs to use
ALLOWED_TRADING_PAIRS = get_env_list("ALLOWED_TRADING_PAIRS", ["BTC", "ETH", "HYPE", "SOL", "BNB"])

# Default slippage percentage
DEFAULT_SLIPPAGE = get_env_float("DEFAULT_SLIPPAGE", 0.01)

# Order timeout (seconds)
ORDER_TIMEOUT = get_env_int("ORDER_TIMEOUT", 30)

# =============================================================================
# POSITION VERIFICATION SETTINGS
# =============================================================================
POSITION_VERIFICATION_RETRIES = get_env_int("POSITION_VERIFICATION_RETRIES", 3)
POSITION_VERIFICATION_DELAY = get_env_int("POSITION_VERIFICATION_DELAY", 5)

# Startup configuration
CLOSE_EXISTING_POSITIONS_ON_START = get_env_bool("CLOSE_EXISTING_POSITIONS_ON_START", True)

# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate Lighter credentials
    if not LIGHTER_API_KEY_PRIVATE_KEY:
        errors.append("LIGHTER_API_KEY_PRIVATE_KEY is required")
    
    # Validate Pacifica credentials
    if not PACIFICA_PRIVATE_KEY:
        errors.append("PACIFICA_PRIVATE_KEY is required")
    
    if PACIFICA_PRIVATE_KEY and len(PACIFICA_PRIVATE_KEY) < 32:
        errors.append("PACIFICA_PRIVATE_KEY appears to be invalid (too short)")
    
    # Validate position hold times
    if MIN_POSITION_HOLD_MINUTES >= MAX_POSITION_HOLD_MINUTES:
        errors.append("MIN_POSITION_HOLD_MINUTES must be less than MAX_POSITION_HOLD_MINUTES")
    
    if MIN_POSITION_HOLD_MINUTES <= 0 or MAX_POSITION_HOLD_MINUTES <= 0:
        errors.append("Position hold times must be greater than 0 minutes")
    
    # Validate trading intervals
    if MIN_TRADE_INTERVAL >= MAX_TRADE_INTERVAL:
        errors.append("MIN_TRADE_INTERVAL must be less than MAX_TRADE_INTERVAL")
    
    # Validate position sizing
    if MIN_POSITION_PERCENT >= MAX_POSITION_PERCENT:
        errors.append("MIN_POSITION_PERCENT must be less than MAX_POSITION_PERCENT")
    
    if MIN_POSITION_PERCENT <= 0 or MAX_POSITION_PERCENT <= 0:
        errors.append("Position percentages must be greater than 0")
    
    if MAX_POSITION_PERCENT > 100:
        errors.append("MAX_POSITION_PERCENT cannot exceed 100%")
    
    if ACCOUNT_BALANCE <= 0:
        errors.append("ACCOUNT_BALANCE must be greater than 0")
    
    # Validate proxy configuration (MANDATORY)
    if USE_PROXY and not PROXY_URL:
        errors.append("PROXY_URL is required when USE_PROXY is true. Proxy usage is mandatory for this bot.")
    
    if USE_PROXY and PROXY_URL:
        if not PROXY_URL.startswith(('http://', 'https://')):
            errors.append("PROXY_URL must start with http:// or https://")
        if '@' not in PROXY_URL:
            errors.append("PROXY_URL must include authentication credentials (username:password@host:port)")
        if "proxy.example.com" in PROXY_URL or "username:password" in PROXY_URL:
            errors.append("PROXY_URL is still using example values. Please update with your actual proxy credentials.")
    
    # Validate trading pairs and leverage
    if not ALLOWED_TRADING_PAIRS:
        errors.append("ALLOWED_TRADING_PAIRS cannot be empty")
    
    for pair in ALLOWED_TRADING_PAIRS:
        if pair not in MANUAL_LEVERAGE:
            errors.append(f"Missing leverage setting for {pair} in MANUAL_LEVERAGE")
    
    for pair, leverage in MANUAL_LEVERAGE.items():
        if leverage <= 0 or leverage > 100:
            errors.append(f"Invalid leverage {leverage} for {pair}. Must be between 0 and 100")
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)

# Validate configuration on import
validate_config()

# =============================================================================
# CONFIGURATION SUMMARY
# =============================================================================
def get_config_summary() -> str:
    """Get a safe configuration summary for logging (no sensitive data)"""
    return f"""
Dual DEX Configuration Summary:
- Account Balance: ${ACCOUNT_BALANCE}
- Position Risk: {MIN_POSITION_PERCENT}%-{MAX_POSITION_PERCENT}%
- Trading Pairs: {', '.join(ALLOWED_TRADING_PAIRS)}
- Leverage Settings: {', '.join(f'{k}:{v}x' for k, v in MANUAL_LEVERAGE.items())}
- Position Hold Time: {MIN_POSITION_HOLD_MINUTES}-{MAX_POSITION_HOLD_MINUTES} minutes
- Wait Between Cycles: {MIN_WAIT_BETWEEN_CYCLES}-{MAX_WAIT_BETWEEN_CYCLES} seconds
- Close Existing Positions: {CLOSE_EXISTING_POSITIONS_ON_START}
- Proxy Enabled: {USE_PROXY}
- Log Level: {LOG_LEVEL}
"""
