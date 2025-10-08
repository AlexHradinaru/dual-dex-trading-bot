#!/usr/bin/env python3
"""
Dual DEX Trading Bot Process Manager

This script provides process management for the dual DEX trading bot:
- Start: Launch the bot in the background
- Stop: Gracefully stop the bot
- Status: Check if the bot is running
- Logs: View bot logs in real-time
- Restart: Stop and start the bot

Usage:
    python3 start_bot.py start    # Start the bot
    python3 start_bot.py stop     # Stop the bot
    python3 start_bot.py status   # Check status
    python3 start_bot.py logs     # View logs
    python3 start_bot.py restart  # Restart the bot
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path


class DualDexBotManager:
    """Process manager for dual DEX trading bot"""
    
    def __init__(self, env_file: str = ".env"):
        self.script_dir = Path(__file__).parent
        self.bot_script = self.script_dir / "dual_dex_bot.py"
        self.env_file = env_file
        
        # Create unique names based on env file
        env_name = Path(env_file).stem  # e.g., ".env.account1" -> "env.account1"
        if env_name == "env":  # Default .env
            self.pid_file = self.script_dir / ".dual_dex_bot.pid"
            self.log_file = self.script_dir / "dual_dex_bot.log"
        else:
            # Use env file name for unique PID and log files
            safe_name = env_name.replace(".", "_")
            self.pid_file = self.script_dir / f".dual_dex_bot_{safe_name}.pid"
            self.log_file = self.script_dir / f"dual_dex_bot_{safe_name}.log"
        
    def is_running(self) -> bool:
        """Check if the bot is currently running"""
        if not self.pid_file.exists():
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)  # This will raise OSError if process doesn't exist
            return True
            
        except (OSError, ValueError, FileNotFoundError):
            # Process doesn't exist or PID file is invalid
            if self.pid_file.exists():
                self.pid_file.unlink()  # Remove stale PID file
            return False
    
    def get_pid(self) -> int:
        """Get the PID of the running bot"""
        if not self.pid_file.exists():
            return None
            
        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None
    
    def start(self) -> bool:
        """Start the bot"""
        if self.is_running():
            print(f"❌ Bot is already running (PID: {self.get_pid()})")
            return False
        
        print(f"🚀 Starting Dual DEX trading bot (env: {self.env_file})...")
        
        # Check if bot script exists
        if not self.bot_script.exists():
            print(f"❌ Bot script not found: {self.bot_script}")
            return False
        
        # Check if .env file exists
        env_file_path = self.script_dir / self.env_file
        if not env_file_path.exists():
            print(f"❌ Env file not found: {env_file_path}")
            print("Please create the env file with proper configuration.")
            return False
        
        try:
            # Prepare environment with custom ENV_FILE variable
            env = os.environ.copy()
            env['DUAL_DEX_ENV_FILE'] = self.env_file
            
            # Start the bot process
            process = subprocess.Popen(
                [sys.executable, str(self.bot_script)],
                cwd=str(self.script_dir),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment to check if process started successfully
            time.sleep(2)
            
            if self.is_running():
                print(f"✅ Bot started successfully (PID: {process.pid})")
                print(f"📋 Log file: {self.log_file}")
                if self.env_file != ".env":
                    print(f"📋 Use 'python3 start_bot.py logs --env {self.env_file}' to view logs")
                    print(f"📋 Use 'python3 start_bot.py status --env {self.env_file}' to check status")
                else:
                    print(f"📋 Use 'python3 start_bot.py logs' to view logs")
                    print(f"📋 Use 'python3 start_bot.py status' to check status")
                return True
            else:
                print("❌ Bot failed to start. Check logs for details.")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the bot"""
        if not self.is_running():
            print("❌ Bot is not running")
            return False
        
        pid = self.get_pid()
        print(f"🛑 Stopping bot (PID: {pid})...")
        
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for i in range(10):  # Wait up to 10 seconds
                if not self.is_running():
                    print("✅ Bot stopped gracefully")
                    return True
                time.sleep(1)
            
            # If still running, force kill
            print("⚠️  Bot didn't stop gracefully, forcing shutdown...")
            os.kill(pid, signal.SIGKILL)
            
            # Wait a bit more
            time.sleep(2)
            
            if not self.is_running():
                print("✅ Bot stopped (forced)")
                return True
            else:
                print("❌ Failed to stop bot")
                return False
                
        except OSError as e:
            print(f"❌ Error stopping bot: {e}")
            return False
        finally:
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
    
    def status(self):
        """Show bot status"""
        if self.is_running():
            pid = self.get_pid()
            print(f"✅ Bot is running (PID: {pid})")
            
            # Show some process info if available
            try:
                # Get process start time and memory usage
                import psutil
                process = psutil.Process(pid)
                create_time = process.create_time()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time))
                uptime_seconds = time.time() - create_time
                uptime_hours = uptime_seconds / 3600
                
                print(f"📊 Started: {start_time}")
                print(f"📊 Uptime: {uptime_hours:.1f} hours")
                print(f"📊 Memory: {memory_mb:.1f} MB")
                
            except ImportError:
                print("📋 Install 'psutil' for detailed process information")
            except Exception as e:
                print(f"📋 Process info unavailable: {e}")
                
        else:
            print("❌ Bot is not running")
        
        # Show log file info
        if self.log_file.exists():
            log_size = self.log_file.stat().st_size / 1024  # KB
            log_modified = time.strftime('%Y-%m-%d %H:%M:%S', 
                                       time.localtime(self.log_file.stat().st_mtime))
            print(f"📄 Log file: {self.log_file} ({log_size:.1f} KB, modified: {log_modified})")
        else:
            print("📄 No log file found")
    
    def logs(self, follow: bool = True):
        """Show bot logs"""
        if not self.log_file.exists():
            print("❌ Log file not found")
            return
        
        if follow:
            print(f"📄 Following logs from {self.log_file}")
            print("📋 Press Ctrl+C to stop following")
            try:
                # Use tail -f equivalent
                subprocess.run(['tail', '-f', str(self.log_file)])
            except KeyboardInterrupt:
                print("\n📋 Stopped following logs")
            except FileNotFoundError:
                # Fallback for systems without tail
                print("📄 Showing recent logs:")
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-50:]:  # Show last 50 lines
                        print(line.rstrip())
        else:
            # Show recent logs
            print("📄 Recent logs:")
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:  # Show last 20 lines
                    print(line.rstrip())
    
    def restart(self) -> bool:
        """Restart the bot"""
        print("🔄 Restarting bot...")
        
        # Stop if running
        if self.is_running():
            if not self.stop():
                return False
        
        # Wait a moment
        time.sleep(1)
        
        # Start again
        return self.start()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Dual DEX Trading Bot Process Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start_bot.py start                          # Start with default .env
  python3 start_bot.py start --env .env.account1      # Start with custom env
  python3 start_bot.py start --env .env.account2      # Start second instance
  python3 start_bot.py stop --env .env.account1       # Stop specific instance
  python3 start_bot.py status                         # Check default instance
  python3 start_bot.py logs --env .env.account1       # View logs for account1
  python3 start_bot.py restart --env .env.account2    # Restart account2
        """
    )
    
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'status', 'logs', 'restart'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--env',
        default='.env',
        help='Path to environment file (default: .env). Use different files for multiple instances.'
    )
    
    parser.add_argument(
        '--no-follow',
        action='store_true',
        help='For logs command: show recent logs instead of following'
    )
    
    args = parser.parse_args()
    
    manager = DualDexBotManager(env_file=args.env)
    
    if args.action == 'start':
        success = manager.start()
        sys.exit(0 if success else 1)
        
    elif args.action == 'stop':
        success = manager.stop()
        sys.exit(0 if success else 1)
        
    elif args.action == 'status':
        manager.status()
        
    elif args.action == 'logs':
        manager.logs(follow=not args.no_follow)
        
    elif args.action == 'restart':
        success = manager.restart()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
