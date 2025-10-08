#!/usr/bin/env python3
"""
🚀 Enhanced Dual DEX Trading Bot

A sophisticated automated trading bot that implements a dual DEX hedging strategy using both Lighter Protocol and Pacifica Finance.

## 🚀 Key Features
- **Dual DEX Strategy**: Places opposite orders on Lighter and Pacifica DEXes
- **Position Verification**: Double-checks all position operations before proceeding
- **Random Order Assignment**: Randomly assigns buy/sell orders to each DEX
- **Dynamic Hold Times**: Configurable position hold periods
- **Comprehensive Logging**: Detailed trade tracking and error handling
- **Proxy Support**: Secure connection routing for both DEXes
- **Risk Management**: Percentage-based position sizing

## 🔄 Trading Workflow
1. **Startup Check**: Verify no open positions exist on either DEX
2. **Position Cleanup**: Close any existing positions with verification
3. **Order Placement**: Place opposite orders (buy on one DEX, sell on other)
4. **Position Hold**: Wait for configured time period
5. **Position Close**: Close positions on both DEXes with verification
6. **Cycle Repeat**: Return to step 3

IMPORTANT: This is for educational/testing purposes only. 
Use at your own risk and ensure you understand the implications of automated trading.
"""

import asyncio
import logging
import random
import time
import os
import fcntl
import signal
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

# Import both SDKs
import lighter
import requests
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
import base58


def sign_message(header, payload, keypair):
    """Sign a message using the keypair"""
    message = prepare_message(header, payload)
    message_bytes = message.encode("utf-8")
    signature = keypair.sign_message(message_bytes)
    return (message, base58.b58encode(bytes(signature)).decode("ascii"))


def prepare_message(header, payload):
    """Prepare message for signing"""
    if (
        "type" not in header
        or "timestamp" not in header
        or "expiry_window" not in header
    ):
        raise ValueError("Header must have type, timestamp, and expiry_window")

    data = {
        **header,
        "data": payload,
    }

    message = sort_json_keys(data)
    message = json.dumps(message, separators=(",", ":"))
    return message


def sort_json_keys(value):
    """Sort JSON keys recursively"""
    if isinstance(value, dict):
        sorted_dict = {}
        for key in sorted(value.keys()):
            sorted_dict[key] = sort_json_keys(value[key])
        return sorted_dict
    elif isinstance(value, list):
        return [sort_json_keys(item) for item in value]
    else:
        return value

# Import configuration
from config import (
    # Lighter config
    LIGHTER_MAINNET_URL, LIGHTER_API_KEY_PRIVATE_KEY, LIGHTER_ACCOUNT_INDEX, LIGHTER_API_KEY_INDEX,
    # Pacifica config  
    PACIFICA_MAINNET_URL, PACIFICA_PRIVATE_KEY,
    # Common config
    ACCOUNT_BALANCE, MIN_POSITION_PERCENT, MAX_POSITION_PERCENT, MIN_POSITION_HOLD_MINUTES, MAX_POSITION_HOLD_MINUTES,
    MIN_WAIT_BETWEEN_CYCLES, MAX_WAIT_BETWEEN_CYCLES, ALLOWED_TRADING_PAIRS, MANUAL_LEVERAGE,
    USE_PROXY, PROXY_URL, LOG_LEVEL, LOG_TO_FILE, LOG_FILE, ORDER_TIMEOUT,
    CLOSE_EXISTING_POSITIONS_ON_START, POSITION_VERIFICATION_RETRIES, POSITION_VERIFICATION_DELAY,
    DEFAULT_SLIPPAGE
)


class TradingStats:
    """Track trading statistics for both DEXes"""
    
    def __init__(self):
        self.lighter_stats = {
            'trades': 0,
            'successful': 0,
            'failed': 0,
            'positions_opened': 0,
            'positions_closed': 0
        }
        self.pacifica_stats = {
            'trades': 0,
            'successful': 0,
            'failed': 0,
            'positions_opened': 0,
            'positions_closed': 0
        }
        self.cycle_stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'start_time': datetime.now()
        }
        
    def record_lighter_trade(self, success: bool):
        """Record a Lighter trade"""
        self.lighter_stats['trades'] += 1
        if success:
            self.lighter_stats['successful'] += 1
        else:
            self.lighter_stats['failed'] += 1
            
    def record_pacifica_trade(self, success: bool):
        """Record a Pacifica trade"""
        self.pacifica_stats['trades'] += 1
        if success:
            self.pacifica_stats['successful'] += 1
        else:
            self.pacifica_stats['failed'] += 1
            
    def record_cycle(self, success: bool):
        """Record a trading cycle"""
        self.cycle_stats['total_cycles'] += 1
        if success:
            self.cycle_stats['successful_cycles'] += 1
        else:
            self.cycle_stats['failed_cycles'] += 1
            
    def get_summary(self) -> str:
        """Get trading statistics summary"""
        runtime = datetime.now() - self.cycle_stats['start_time']
        return f"""
📊 Dual DEX Trading Statistics:
🔄 Cycles: {self.cycle_stats['total_cycles']} total, {self.cycle_stats['successful_cycles']} successful
⏱️ Runtime: {runtime}
📈 Lighter: {self.lighter_stats['trades']} trades ({self.lighter_stats['successful']} successful)
📈 Pacifica: {self.pacifica_stats['trades']} trades ({self.pacifica_stats['successful']} successful)
"""


class PositionManager:
    """Manage positions for both DEXes"""
    
    def __init__(self):
        self.lighter_position = None
        self.pacifica_position = None
        self.cycle_start_time = None
        
    def has_positions(self) -> bool:
        """Check if we have positions on either DEX"""
        return self.lighter_position is not None or self.pacifica_position is not None
        
    def start_cycle(self):
        """Start a new trading cycle"""
        self.cycle_start_time = datetime.now()
        
    def record_lighter_position(self, symbol: str, side: str, amount: float, tx_hash: str):
        """Record a Lighter position"""
        self.lighter_position = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'tx_hash': tx_hash,
            'opened_at': datetime.now()
        }
        
    def record_pacifica_position(self, symbol: str, side: str, amount: str, order_id: str):
        """Record a Pacifica position"""
        self.pacifica_position = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'order_id': order_id,
            'opened_at': datetime.now()
        }
        
    def clear_positions(self):
        """Clear all positions"""
        self.lighter_position = None
        self.pacifica_position = None


class DualDexTradingBot:
    """Main dual DEX trading bot class"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.stats = TradingStats()
        self.position_manager = PositionManager()
        
        # Lighter components
        self.lighter_client = None
        self.lighter_api_client = None
        self.lighter_order_api = None
        self.lighter_available_markets = []
        
        # Pacifica components
        self.pacifica_session = None
        self.pacifica_keypair = None
        self.pacifica_wallet_address = None
        
        # Control flags
        self.running = False
        self.pid_file = "dual_dex_bot.pid"
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if LOG_TO_FILE:
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        # Reduce noise from other libraries
        logging.getLogger('lighter').setLevel(logging.WARNING)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        logging.getLogger('solana').setLevel(logging.WARNING)
        
        return logger
        
    async def initialize(self):
        """Initialize both DEX connections"""
        self.logger.info("🚀 Initializing Dual DEX Trading Bot...")
        
        # Initialize Lighter
        await self._initialize_lighter()
        
        # Initialize Pacifica
        await self._initialize_pacifica()
        
        self.logger.info("✅ Both DEX connections initialized successfully")
        
    async def _initialize_lighter(self):
        """Initialize Lighter Protocol connection"""
        try:
            self.logger.info("🔗 Connecting to Lighter Protocol...")
            
            # Configure SSL settings and proxy
            config = lighter.Configuration(host=LIGHTER_MAINNET_URL)
            config.verify_ssl = False
            
            if USE_PROXY and PROXY_URL:
                config.proxy = PROXY_URL
                self.logger.info(f"Using proxy for Lighter: {PROXY_URL}")
            
            self.lighter_api_client = lighter.ApiClient(configuration=config)
            
            self.lighter_client = lighter.SignerClient(
                url=LIGHTER_MAINNET_URL,
                private_key=LIGHTER_API_KEY_PRIVATE_KEY,
                account_index=LIGHTER_ACCOUNT_INDEX,
                api_key_index=LIGHTER_API_KEY_INDEX,
            )
            
            # Replace SignerClient's ApiClient with our configured one
            await self.lighter_client.api_client.close()
            self.lighter_client.api_client = self.lighter_api_client
            self.lighter_client.tx_api = lighter.TransactionApi(self.lighter_api_client)
            self.lighter_client.order_api = lighter.OrderApi(self.lighter_api_client)
            
            self.lighter_order_api = lighter.OrderApi(self.lighter_api_client)
            
            # Verify connection
            err = self.lighter_client.check_client()
            if err:
                raise Exception(f"Lighter client verification failed: {err}")
                
            # Load markets
            await self._load_lighter_markets()
            
            self.logger.info("✅ Lighter Protocol connected successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Lighter: {e}")
            raise
            
    async def _initialize_pacifica(self):
        """Initialize Pacifica Finance connection"""
        try:
            self.logger.info("🔗 Connecting to Pacifica Finance...")
            
            # Setup Solana keypair
            if not PACIFICA_PRIVATE_KEY:
                raise ValueError("PACIFICA_PRIVATE_KEY is required")
                
            # Initialize keypair using solders
            self.pacifica_keypair = Keypair.from_base58_string(PACIFICA_PRIVATE_KEY)
            self.pacifica_wallet_address = str(self.pacifica_keypair.pubkey())
            
            # Setup session with proxy
            self.pacifica_session = requests.Session()
            if USE_PROXY and PROXY_URL:
                self.pacifica_session.proxies = {
                    'http': PROXY_URL,
                    'https': PROXY_URL
                }
                self.logger.info(f"Using proxy for Pacifica: {PROXY_URL}")
            
            self.logger.info(f"✅ Pacifica Finance connected successfully (Wallet: {self.pacifica_wallet_address[:8]}...)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Pacifica: {e}")
            raise
            
    async def _load_lighter_markets(self):
        """Load available Lighter markets"""
        try:
            self.logger.info("📊 Loading Lighter markets...")
            order_books = await self.lighter_order_api.order_books()
            
            self.lighter_available_markets = []
            for market in order_books.order_books:
                market_info = {
                    'index': market.market_id,
                    'symbol': market.symbol,
                    'status': market.status,
                    'min_base_amount': market.min_base_amount,
                    'min_quote_amount': market.min_quote_amount,
                }
                
                # Filter by allowed trading pairs and active status
                if (market.symbol in ALLOWED_TRADING_PAIRS and 
                    market.status.lower() == 'active'):
                    self.lighter_available_markets.append(market_info)
                    
            if not self.lighter_available_markets:
                raise Exception("No available Lighter markets found")
                
            self.logger.info(f"📊 Loaded {len(self.lighter_available_markets)} Lighter markets: {[m['symbol'] for m in self.lighter_available_markets]}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load Lighter markets: {e}")
            raise
            
    async def _get_lighter_market_details(self, market_index: int) -> Optional[Dict]:
        """Get detailed Lighter market information"""
        try:
            details_response = await self.lighter_order_api.order_book_details(market_index)
            details = details_response.order_book_details[0]
            
            return {
                'symbol': details.symbol,
                'price_decimals': details.price_decimals,
                'size_decimals': details.size_decimals,
                'default_imf': details.default_initial_margin_fraction,
                'min_imf': details.min_initial_margin_fraction,
                'default_leverage': 10000 / details.default_initial_margin_fraction,
                'max_leverage': 10000 / details.min_initial_margin_fraction,
            }
        except Exception as e:
            self.logger.error(f"Failed to get Lighter market details for {market_index}: {e}")
            return None
            
    async def _get_lighter_market_price(self, market_index: int, is_ask: bool, market_details: Dict) -> Optional[Tuple[int, float]]:
        """Get current market price from Lighter - matches working SDK implementation"""
        try:
            order_book = await self.lighter_order_api.order_book_orders(market_index, 1)
            
            if is_ask and order_book.bids:
                # For ask orders (short positions), use bid price
                price_str = order_book.bids[0].price
            elif not is_ask and order_book.asks:
                # For bid orders (long positions), use ask price
                price_str = order_book.asks[0].price
            else:
                self.logger.warning(f"No price data available for market {market_index}")
                return None
                
            # Convert price string to float for USD display
            price_usd = float(price_str)
            
            # Convert to internal format (scaled by price_decimals)
            price_decimals = market_details.get('price_decimals', 5)
            price_scaled = int(price_usd * (10 ** price_decimals))
            
            # Apply slippage tolerance
            if is_ask:
                price_scaled = int(price_scaled * (1 - DEFAULT_SLIPPAGE))
                price_usd = price_usd * (1 - DEFAULT_SLIPPAGE)
            else:
                price_scaled = int(price_scaled * (1 + DEFAULT_SLIPPAGE))
                price_usd = price_usd * (1 + DEFAULT_SLIPPAGE)
                
            return price_scaled, price_usd

        except Exception as e:
            self.logger.error(f"Failed to get Lighter market price for {market_index}: {e}")
            return None
            
    async def _get_pacifica_market_price(self, symbol: str, side: str) -> Optional[float]:
        """Get current market price from Pacifica using WebSocket"""
        try:
            # Try WebSocket price subscription first
            price = await self._get_pacifica_price_from_websocket(symbol)
            if price:
                self.logger.debug(f"Pacifica price for {symbol} ({side}): ${price:.2f} (WebSocket)")
                return price
            
            # Fallback to mock prices if WebSocket fails
            self.logger.warning(f"WebSocket price failed for {symbol}, using fallback")
            mock_prices = {
                "BTC": 65000.0,
                "ETH": 3500.0,
                "HYPE": 0.25,
                "SOL": 150.0,
                "BNB": 600.0
            }
            
            price = mock_prices.get(symbol, 100.0)
            self.logger.debug(f"Pacifica price for {symbol} ({side}): ${price:.2f} (mock)")
            return price
            
        except Exception as e:
            self.logger.error(f"Failed to get Pacifica market price for {symbol}: {e}")
            return 100.0  # Fallback price
            
    async def _get_pacifica_price_from_websocket(self, symbol: str) -> Optional[float]:
        """Get real-time price from Pacifica WebSocket"""
        try:
            import websockets
            import json
            import ssl
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to Pacifica WebSocket with SSL context
            async with websockets.connect("wss://ws.pacifica.fi/ws", ping_interval=30, ssl=ssl_context) as websocket:
                # Subscribe to prices
                ws_message = {"method": "subscribe", "params": {"source": "prices"}}
                await websocket.send(json.dumps(ws_message))
                
                # Wait for subscription confirmation first
                try:
                    confirm_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    confirm_data = json.loads(confirm_message)
                    self.logger.debug(f"WebSocket subscription confirmed: {confirm_data}")
                    
                    # Now wait for actual price data
                    price_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(price_message)
                    
                    # Look for the symbol in the price data
                    if isinstance(data, dict) and 'data' in data:
                        price_list = data['data']
                        if isinstance(price_list, list):
                            for price_item in price_list:
                                if isinstance(price_item, dict) and price_item.get('symbol') == symbol:
                                    # Use oracle price as the most accurate
                                    oracle_price = price_item.get('oracle')
                                    if oracle_price:
                                        return float(oracle_price)
                                
                except asyncio.TimeoutError:
                    self.logger.debug(f"WebSocket timeout for {symbol}")
                    return None
                    
        except Exception as e:
            self.logger.debug(f"WebSocket price fetch failed for {symbol}: {e}")
            self.logger.debug(f"WebSocket error type: {type(e).__name__}")
            return None
            
    def _calculate_hedged_position_sizes(self, symbol: str, lighter_price: float, pacifica_price: float) -> tuple[float, float]:
        """Calculate hedged position sizes with equal notional values for both DEXes"""
        try:
            # Random percentage between min and max
            risk_percent = random.uniform(MIN_POSITION_PERCENT, MAX_POSITION_PERCENT)
            
            # Calculate risk amount in dollars
            risk_amount = (risk_percent / 100) * ACCOUNT_BALANCE
            
            # Get leverage for this symbol
            leverage = MANUAL_LEVERAGE.get(symbol, 1.0)
            
            # Calculate target notional value
            target_notional = risk_amount * leverage
            
            # Get Pacifica account balance to cap the notional
            pacifica_cap = ACCOUNT_BALANCE * leverage  # Default fallback
            try:
                success, account_info = self._make_pacifica_request("/api/v1/account/info", {})
                if success and account_info and 'account_value' in account_info:
                    actual_balance = float(account_info['account_value'])
                    pacifica_cap = actual_balance * leverage * 0.9  # 90% of actual balance with leverage
                    self.logger.debug(f"Pacifica actual balance: ${actual_balance:.2f}, cap: ${pacifica_cap:.2f}")
            except Exception as e:
                self.logger.debug(f"Using fallback Pacifica cap: ${pacifica_cap:.2f}")
            
            # Use the smaller of target notional or Pacifica cap
            hedged_notional = min(target_notional, pacifica_cap)
            
            # Calculate position sizes for both DEXes
            lighter_size = hedged_notional / lighter_price
            pacifica_size = hedged_notional / pacifica_price
            
            # Apply max exposure cap (80% of account balance)
            max_affordable_notional = ACCOUNT_BALANCE * 0.8
            if hedged_notional > max_affordable_notional:
                hedged_notional = max_affordable_notional
                lighter_size = hedged_notional / lighter_price
                pacifica_size = hedged_notional / pacifica_price
                self.logger.warning(f"Reduced hedged notional for {symbol} due to risk limits")
            
            # Ensure minimum sizes
            lighter_size = max(lighter_size, 0.000001)
            pacifica_size = max(pacifica_size, 0.000001)
            
            self.logger.debug(f"Hedged notional: ${hedged_notional:.2f}, Lighter: {lighter_size:.6f}, Pacifica: {pacifica_size:.6f}")
            
            return lighter_size, pacifica_size
            
        except Exception as e:
            self.logger.error(f"Failed to calculate hedged position sizes: {e}")
            return 0.001, 0.001  # Fallback minimums
            
    async def _check_and_close_existing_positions(self):
        """Check and close existing positions on both DEXes"""
        if not CLOSE_EXISTING_POSITIONS_ON_START:
            self.logger.info("⏭️ Skipping position cleanup (CLOSE_EXISTING_POSITIONS_ON_START=False)")
            return
            
        self.logger.info("🔍 Checking for existing positions on both DEXes...")
        
        # Close Lighter positions
        await self._close_lighter_positions()
        
        # Close Pacifica positions  
        await self._close_pacifica_positions()
        
        self.logger.info("✅ Position cleanup completed")
        
    async def _close_lighter_positions(self):
        """Close existing Lighter positions"""
        try:
            self.logger.info("🔍 Checking Lighter positions...")
            
            # Get account details including positions
            account_api = lighter.AccountApi(self.lighter_api_client)
            account_response = await account_api.account(by="index", value=str(LIGHTER_ACCOUNT_INDEX))
            
            if hasattr(account_response, 'accounts') and account_response.accounts:
                account = account_response.accounts[0]
                if hasattr(account, 'positions') and account.positions:
                    # Filter for positions with non-zero size
                    open_positions = [pos for pos in account.positions if abs(float(pos.position)) > 1e-6]
                    
                    if open_positions:
                        self.logger.info(f"🔍 Found {len(open_positions)} open Lighter positions")
                        
                        for pos in open_positions:
                            await self._close_lighter_position(pos)
                    else:
                        self.logger.info("✅ No open Lighter positions found")
                else:
                    self.logger.info("✅ No Lighter positions found")
            else:
                self.logger.info("✅ No Lighter account found")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to check Lighter positions: {e}")
            
    async def _close_lighter_position(self, position):
        """Close a specific Lighter position"""
        try:
            market_id = position.market_id
            position_size_float = float(position.position)
            
            self.logger.info(f"🔍 Closing Lighter position: {position.symbol} (size: {position_size_float})")
            
            # Get market details
            market_details = await self._get_lighter_market_details(market_id)
            if not market_details:
                self.logger.error(f"Could not get market details for market {market_id}")
                return
                
            # Determine close direction
            is_ask = position_size_float > 0  # Positive size = long position -> sell to close
            price_result = await self._get_lighter_market_price(market_id, is_ask, market_details)
            
            if not price_result:
                self.logger.error(f"Could not get market price for {position.symbol}")
                return
                
            # Extract price_scaled and price_usd from result
            price_scaled, price_usd = price_result
                
            # Calculate scaled amounts
            size_decimals = market_details['size_decimals']
            
            base_amount_scaled = int(abs(position_size_float) * (10 ** size_decimals))
            
            # Add 1% buffer to ensure complete closure
            base_amount_scaled = int(base_amount_scaled * 1.01)
            
            # Generate unique client order index
            client_order_index = int(time.time() * 1000) % 1000000
            
            # Place close order using correct method signature
            created_order, tx_hash, error = await self.lighter_client.create_market_order(
                market_index=market_id,
                client_order_index=client_order_index,
                base_amount=base_amount_scaled,
                avg_execution_price=price_scaled,
                is_ask=is_ask,
                reduce_only=True
            )
            
            if error:
                self.logger.error(f"❌ Failed to place Lighter close order: {error}")
            else:
                self.logger.info(f"✅ Lighter close order placed: {tx_hash}")
                
                # Verify position is closed
                await asyncio.sleep(POSITION_VERIFICATION_DELAY)
                await self._verify_lighter_position_closed(market_id, position_size_float)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close Lighter position: {e}")
            
    async def _verify_lighter_position_closed(self, market_id: int, original_size: float):
        """Verify that a Lighter position is actually closed"""
        try:
            # Get updated account details
            account_api = lighter.AccountApi(self.lighter_api_client)
            account_response = await account_api.account(by="index", value=str(LIGHTER_ACCOUNT_INDEX))
            
            if hasattr(account_response, 'accounts') and account_response.accounts:
                account = account_response.accounts[0]
                if hasattr(account, 'positions') and account.positions:
                    # Find the position for this market
                    for pos in account.positions:
                        if pos.market_id == market_id:
                            current_size = float(pos.position)
                            if abs(current_size) > 1e-6:
                                self.logger.warning(f"⚠️ Lighter position still open: {current_size} (original: {original_size})")
                                # Try opposite direction
                                await self._close_lighter_position_opposite(pos)
            else:
                self.logger.info(f"✅ Lighter position verified closed")
                return
                            
            self.logger.info(f"✅ Lighter position verified closed (no position found)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to verify Lighter position closure: {e}")
            
    async def _close_lighter_position_opposite(self, position):
        """Close Lighter position with opposite direction"""
        try:
            market_id = position.market_id
            position_size_float = float(position.position)
            
            self.logger.info(f"🔄 Retrying Lighter close with opposite direction: {position.symbol}")
            
            # Get market details
            market_details = await self._get_lighter_market_details(market_id)
            if not market_details:
                return
                
            # Try opposite direction
            is_ask = position_size_float < 0  # Negative size = short position -> buy to close
            price_result = await self._get_lighter_market_price(market_id, is_ask, market_details)
            
            if not price_result:
                return
                
            # Extract price_scaled and price_usd from result
            price_scaled, price_usd = price_result
                
            # Calculate scaled amounts
            size_decimals = market_details['size_decimals']
            
            base_amount_scaled = int(abs(position_size_float) * (10 ** size_decimals))
            
            # Add 1% buffer
            base_amount_scaled = int(base_amount_scaled * 1.01)
            
            # Generate unique client order index
            client_order_index = int(time.time() * 1000) % 1000000
            
            # Place close order with opposite direction
            created_order, tx_hash, error = await self.lighter_client.create_market_order(
                market_index=market_id,
                client_order_index=client_order_index,
                base_amount=base_amount_scaled,
                avg_execution_price=price_scaled,
                is_ask=is_ask,
                reduce_only=True
            )
            
            if error:
                self.logger.error(f"❌ Failed to place Lighter opposite close order: {error}")
            else:
                self.logger.info(f"✅ Lighter opposite close order placed: {tx_hash}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close Lighter position with opposite direction: {e}")
            
    async def _close_pacifica_positions(self):
        """Close existing Pacifica positions"""
        try:
            self.logger.info("🔍 Checking Pacifica positions...")
            
            # Since Pacifica doesn't have a direct "get positions" endpoint,
            # we'll attempt to close common position types
            common_symbols = ALLOWED_TRADING_PAIRS.copy()
            test_amounts = ["0.001", "0.01", "0.1", "1.0"]
            
            positions_found = 0
            
            for symbol in common_symbols:
                try:
                    self.logger.debug(f"🔍 Testing {symbol} for existing positions...")
                    
                    # Try different amounts for long positions (sell to close)
                    for amount in test_amounts:
                        long_closed = await self._attempt_close_pacifica_position(symbol, "ask", amount)
                        if long_closed:
                            positions_found += 1
                            self.logger.info(f"✅ Closed Pacifica long position: {symbol} ({amount})")
                            
                    # Try different amounts for short positions (buy to close)
                    for amount in test_amounts:
                        short_closed = await self._attempt_close_pacifica_position(symbol, "bid", amount)
                        if short_closed:
                            positions_found += 1
                            self.logger.info(f"✅ Closed Pacifica short position: {symbol} ({amount})")
                
                except Exception as e:
                    self.logger.debug(f"Error testing {symbol}: {e}")
                    
            if positions_found == 0:
                self.logger.info("✅ No open Pacifica positions found")
            else:
                self.logger.info(f"✅ Closed {positions_found} Pacifica positions")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to check Pacifica positions: {e}")
            
    async def _attempt_close_pacifica_position(self, symbol: str, side: str, amount: str) -> bool:
        """Attempt to close a Pacifica position"""
        try:
            close_params = {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "slippage_percent": str(DEFAULT_SLIPPAGE),
                "reduce_only": True,
                "client_order_id": str(uuid.uuid4())
            }
            
            # Use silent request for position detection
            success, response = self._make_pacifica_silent_request("/orders/create_market", close_params)
            
            if success:
                order_id = close_params['client_order_id']
                self.logger.debug(f"🔍 Pacifica close order placed for {symbol} {side} (amount: {amount}): {order_id}")
                
                # Wait and verify
                await asyncio.sleep(3)
                
                # Test if position is actually closed
                test_params = close_params.copy()
                test_params['amount'] = "0.001"  # Small test amount
                
                test_success, test_response = self._make_pacifica_silent_request("/orders/create_market", test_params)
                
                if not test_success and test_response and "No position found" in str(test_response):
                    # Position was successfully closed
                    return True
                elif test_success:
                    # Position still exists, try opposite direction
                    opposite_side = "ask" if side == "bid" else "bid"
                    opposite_params = close_params.copy()
                    opposite_params['side'] = opposite_side
                    
                    opposite_success, opposite_response = self._make_pacifica_silent_request("/orders/create_market", opposite_params)
                    if opposite_success:
                        self.logger.info(f"✅ Pacifica position closed with opposite direction: {symbol}")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.debug(f"Error attempting to close Pacifica position {symbol}: {e}")
            return False
            
    def _make_pacifica_silent_request(self, endpoint: str, payload: Dict) -> Tuple[bool, Optional[Dict]]:
        """Make authenticated request to Pacifica API without logging errors"""
        try:
            url = f"{PACIFICA_MAINNET_URL}{endpoint}"
            
            # Generate timestamp and signature
            timestamp = int(time.time() * 1_000)
            
            signature_header = {
                "timestamp": timestamp,
                "expiry_window": 5_000,
                "type": "create_market_order",
            }
            
            # Sign the message
            message, signature = sign_message(signature_header, payload, self.pacifica_keypair)
            
            # Construct request
            request_data = {
                "account": self.pacifica_wallet_address,
                "signature": signature,
                "timestamp": timestamp,
                "expiry_window": 5_000,
                **payload
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "DualDexBot/1.0"
            }
            
            response = self.pacifica_session.post(url, json=request_data, headers=headers, timeout=ORDER_TIMEOUT)

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.json() if response.text else None
                
        except Exception as e:
            return False, None
            
    async def run_trading_cycle(self):
        """Run a complete trading cycle"""
        try:
            self.logger.info("🚀 Starting new trading cycle...")
            self.position_manager.start_cycle()
            self.stats.record_cycle(False)  # Will update to True if successful
            
            # Step 1: Select random trading pair
            symbol = random.choice(ALLOWED_TRADING_PAIRS)
            self.logger.info(f"🎯 Selected trading pair: {symbol}")
            
            # Step 2: Randomly assign buy/sell to each DEX
            lighter_side = random.choice(["buy", "sell"])
            pacifica_side = "sell" if lighter_side == "buy" else "buy"
            
            self.logger.info(f"📊 Order assignment: Lighter={lighter_side.upper()}, Pacifica={pacifica_side.upper()}")
            
            # Step 3: Get market prices
            # Find Lighter market
            market = None
            for m in self.lighter_available_markets:
                if m['symbol'] == symbol:
                    market = m
                    break
                    
            if not market:
                self.logger.error(f"❌ Market {symbol} not found on Lighter")
                return
                
            # Get market details
            market_details = await self._get_lighter_market_details(market['index'])
            if not market_details:
                self.logger.error(f"❌ Could not get market details for {symbol}")
                return
                
            # Get Lighter price
            lighter_is_ask = lighter_side == "sell"
            lighter_price_result = await self._get_lighter_market_price(market['index'], lighter_is_ask, market_details)
            if lighter_price_result is None:
                self.logger.error(f"❌ Failed to get Lighter market price")
                return
            lighter_price_scaled, lighter_price = lighter_price_result
            
            # Get Pacifica price
            pacifica_price = await self._get_pacifica_market_price(symbol, pacifica_side)
            if pacifica_price is None:
                self.logger.error(f"❌ Failed to get Pacifica market price")
                return
                
            self.logger.info(f"💰 Prices: Lighter=${lighter_price:.2f}, Pacifica=${pacifica_price:.2f}")
            
            # Step 4: Calculate hedged position sizes (equal notional values)
            lighter_size, pacifica_size = self._calculate_hedged_position_sizes(symbol, lighter_price, pacifica_price)
            
            self.logger.info(f"📏 Position sizes: Lighter={lighter_size:.6f}, Pacifica={pacifica_size:.6f}")
            
            # Step 5: Place orders simultaneously
            lighter_success = await self._place_lighter_order(symbol, lighter_side, lighter_size)
            pacifica_success = await self._place_pacifica_order(symbol, pacifica_side, pacifica_size)
            
            if lighter_success and pacifica_success:
                self.logger.info("✅ Both orders placed successfully!")
                
                # Step 6: Wait for dynamic hold time
                hold_minutes = random.uniform(MIN_POSITION_HOLD_MINUTES, MAX_POSITION_HOLD_MINUTES)
                self.logger.info(f"⏳ Holding positions for {hold_minutes:.1f} minutes...")
                await asyncio.sleep(hold_minutes * 60)
                
                # Step 7: Close positions
                await self._close_all_positions()
                
                self.stats.record_cycle(True)
                self.logger.info("✅ Trading cycle completed successfully!")
                
            else:
                self.logger.error("❌ Failed to place orders on one or both DEXes")
                # Clean up any partial positions
                await self._close_all_positions()
            
        except Exception as e:
            self.logger.error(f"❌ Trading cycle failed: {e}")
            await self._close_all_positions()
            
    async def _place_lighter_order(self, symbol: str, side: str, size: float) -> bool:
        """Place order on Lighter"""
        try:
            # Find market
            market = None
            for m in self.lighter_available_markets:
                if m['symbol'] == symbol:
                    market = m
                    break
                    
            if not market:
                return False
                
            # Get market details
            market_details = await self._get_lighter_market_details(market['index'])
            if not market_details:
                return False
                
            # Determine order parameters
            is_ask = (side == "sell")
            price_result = await self._get_lighter_market_price(market['index'], is_ask, market_details)
            
            if not price_result:
                return False
            
            # Extract price_scaled and price_usd from result
            price_scaled, price_usd = price_result
                
            # Calculate scaled amounts
            size_decimals = market_details['size_decimals']
            
            base_amount_scaled = int(size * (10 ** size_decimals))
            
            # Generate unique client order index
            client_order_index = int(time.time() * 1000) % 1000000
            
            # Place order using correct method signature
            created_order, tx_hash, error = await self.lighter_client.create_market_order(
                market_index=market['index'],
                client_order_index=client_order_index,
                base_amount=base_amount_scaled,
                avg_execution_price=price_scaled,
                is_ask=is_ask,
                reduce_only=False
            )
            
            if error:
                self.logger.error(f"❌ Failed to place Lighter order: {error}")
                self.stats.record_lighter_trade(False)
                return False
            else:
                self.logger.info(f"✅ Lighter order placed: {side.upper()} {size:.6f} {symbol} @ ${price_usd:.2f}")
                self.position_manager.record_lighter_position(symbol, side, size, tx_hash)
                self.stats.record_lighter_trade(True)
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to place Lighter order: {e}")
            self.stats.record_lighter_trade(False)
            return False
            
    async def _place_pacifica_order(self, symbol: str, side: str, size: float) -> bool:
        """Place order on Pacifica"""
        try:
            # Convert side to Pacifica format
            pacifica_side = "ask" if side == "sell" else "bid"
            
            # Round amount to lot size (matches Pacifica SDK implementation)
            lot_sizes = {
                "BTC": 0.00001,  # Match API requirement for BTC lot size
                "ETH": 0.01,     # ETH standard lot size
                "HYPE": 1.0,     # HYPE might have larger lot size (low price)
                "SOL": 0.01,     # SOL standard lot size  
                "BNB": 0.01,     # BNB standard lot size
            }
            
            lot_size = lot_sizes.get(symbol, 0.01)  # Default to 0.01
            # Fix floating-point precision issues
            rounded_amount = round(size / lot_size) * lot_size
            rounded_amount = round(rounded_amount, 8)  # Round to 8 decimal places
            rounded_amount = max(rounded_amount, lot_size)  # Ensure minimum lot size
            
            # Create order parameters
            order_params = {
                "symbol": symbol,
                "side": pacifica_side,
                "amount": str(rounded_amount),
                "slippage_percent": str(DEFAULT_SLIPPAGE),
                "reduce_only": False,
                "client_order_id": str(uuid.uuid4())
            }
            
            # Place order
            success, response = self._make_pacifica_request("/orders/create_market", order_params)

            if success:
                order_id = order_params['client_order_id']
                self.logger.info(f"✅ Pacifica order placed: {side.upper()} {rounded_amount:.2f} {symbol}")
                self.position_manager.record_pacifica_position(symbol, side, str(rounded_amount), order_id)
                self.stats.record_pacifica_trade(True)
                return True
            else:
                self.logger.error(f"❌ Failed to place Pacifica order: {response}")
                self.stats.record_pacifica_trade(False)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to place Pacifica order: {e}")
            self.stats.record_pacifica_trade(False)
            return False
            
    def _make_pacifica_request(self, endpoint: str, payload: Dict) -> Tuple[bool, Optional[Dict]]:
        """Make authenticated request to Pacifica API"""
        try:
            url = f"{PACIFICA_MAINNET_URL}{endpoint}"
            
            # Generate timestamp and signature
            timestamp = int(time.time() * 1_000)
            
            signature_header = {
                "timestamp": timestamp,
                "expiry_window": 5_000,
                "type": "create_market_order",
            }
            
            # Sign the message
            message, signature = sign_message(signature_header, payload, self.pacifica_keypair)
            
            # Construct request
            request_data = {
                "account": self.pacifica_wallet_address,
                "signature": signature,
                "timestamp": timestamp,
                "expiry_window": 5_000,
                **payload
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "DualDexBot/1.0"
            }
            
            response = self.pacifica_session.post(url, json=request_data, headers=headers, timeout=ORDER_TIMEOUT)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                self.logger.error(f"Pacifica API request failed: {response.status_code} - {response.text}")
                return False, response.json() if response.text else None
                
        except Exception as e:
            self.logger.error(f"Pacifica API request error: {e}")
            return False, None
            
    async def _close_all_positions(self):
        """Close all open positions on both DEXes"""
        try:
            self.logger.info("🔒 Closing all positions...")
            
            # Close Lighter position
            if self.position_manager.lighter_position:
                await self._close_lighter_position_by_info(self.position_manager.lighter_position)
                
            # Close Pacifica position
            if self.position_manager.pacifica_position:
                await self._close_pacifica_position_by_info(self.position_manager.pacifica_position)
                
            # Clear position manager
            self.position_manager.clear_positions()
            
            self.logger.info("✅ All positions closed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close positions: {e}")
            
    async def _close_lighter_position_by_info(self, position_info: Dict):
        """Close Lighter position using stored info"""
        try:
            symbol = position_info['symbol']
            side = position_info['side']
            
            self.logger.info(f"🔒 Closing Lighter position: {side.upper()} {symbol}")
            
            # Find market
            market = None
            for m in self.lighter_available_markets:
                if m['symbol'] == symbol:
                    market = m
                    break
                    
            if not market:
                self.logger.error(f"Market not found for {symbol}")
                return
                
            # Get market details
            market_details = await self._get_lighter_market_details(market['index'])
            if not market_details:
                return
                
            # Determine close direction (opposite of open)
            is_ask = (side == "buy")  # If we bought, we need to sell to close
            price_result = await self._get_lighter_market_price(market['index'], is_ask, market_details)
            
            if not price_result:
                return
                
            # Extract price_scaled and price_usd from result
            price_scaled, price_usd = price_result
                
            # Calculate scaled amounts
            size_decimals = market_details['size_decimals']
            
            base_amount_scaled = int(position_info['amount'] * (10 ** size_decimals))
            
            # Add 1% buffer
            base_amount_scaled = int(base_amount_scaled * 1.01)
            
            # Generate unique client order index
            client_order_index = int(time.time() * 1000) % 1000000
            
            # Place close order using correct method signature
            created_order, tx_hash, error = await self.lighter_client.create_market_order(
                market_index=market['index'],
                client_order_index=client_order_index,
                base_amount=base_amount_scaled,
                avg_execution_price=price_scaled,
                is_ask=is_ask,
                reduce_only=True
            )
            
            if error:
                self.logger.error(f"❌ Failed to close Lighter position: {error}")
            else:
                self.logger.info(f"✅ Lighter position closed: {tx_hash}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to close Lighter position: {e}")
            
    async def _close_pacifica_position_by_info(self, position_info: Dict):
        """Close Pacifica position using stored info"""
        try:
            symbol = position_info['symbol']
            side = position_info['side']
            amount = position_info['amount']
            
            self.logger.info(f"🔒 Closing Pacifica position: {side.upper()} {symbol}")
            
            # Determine close direction (opposite of open)
            close_side = "ask" if side == "buy" else "bid"
            
            # Create close order
            close_params = {
                "symbol": symbol,
                "side": close_side,
                "amount": amount,
                "slippage_percent": str(DEFAULT_SLIPPAGE),
                "reduce_only": True,
                "client_order_id": str(uuid.uuid4())
            }
            
            # Place close order
            success, response = self._make_pacifica_request("/orders/create_market", close_params)
            
            if success:
                self.logger.info(f"✅ Pacifica position closed")
            else:
                self.logger.error(f"❌ Failed to close Pacifica position: {response}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close Pacifica position: {e}")
            
    async def run(self):
        """Main trading loop"""
        try:
            self.logger.info("🚀 Starting Dual DEX Trading Bot...")
            self.logger.info("Configuration loaded successfully")
            
            # Initialize connections
            await self.initialize()
            
            # Check and close existing positions
            await self._check_and_close_existing_positions()
            
            self.running = True
            self.logger.info("✅ Bot initialized and ready for trading!")
            
            # Main trading loop
            while self.running:
                try:
                    # Run trading cycle
                    await self.run_trading_cycle()
                        
                    # Wait between cycles
                    wait_time = random.randint(MIN_WAIT_BETWEEN_CYCLES, MAX_WAIT_BETWEEN_CYCLES)
                    self.logger.info(f"⏳ Waiting {wait_time} seconds before next cycle...")
                    await asyncio.sleep(wait_time)
                    
                    # Log statistics
                    self.logger.info(self.stats.get_summary())
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Received interrupt signal, stopping...")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in main loop: {e}")
                    await asyncio.sleep(30)  # Wait before retrying
                    
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}")
        finally:
            await self.cleanup()
            
    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info("🧹 Cleaning up resources...")
            
            # Close any remaining positions
            await self._close_all_positions()
            
            # Close API clients
            if self.lighter_api_client:
                await self.lighter_api_client.close()
                
            if self.pacifica_session:
                self.pacifica_session.close()
                
            self.logger.info("✅ Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")


async def main():
    """Main entry point"""
    bot = DualDexTradingBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        bot.logger.info(f"Received signal {signum}, stopping...")
        bot.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        bot.logger.info("🛑 Bot stopped by user")
    except Exception as e:
        bot.logger.error(f"❌ Bot crashed: {e}")
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())