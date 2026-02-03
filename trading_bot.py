import asyncio
import signal
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from trader import Trader
from config import Config
from logger import setup_logger

logger = setup_logger('polymarket_bot')

class TradingBot:
    """Main trading bot with self-healing capabilities"""
    
    def __init__(self):
        self.trader = None
        self.running = False
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        self.error_count = 0
        self.max_errors = 5
        self.restart_delay = 30  # seconds
        
    async def initialize(self):
        """Initialize the trading bot"""
        try:
            logger.info("Initializing Polymarket Trading Bot")
            
            # Validate configuration (skip in test mode)
            try:
                Config.validate()
            except ValueError as e:
                logger.warning(f"Configuration validation skipped: {e}")
            
            # Initialize trader
            self.trader = Trader()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("Trading bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading bot: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def health_check(self) -> bool:
        """Perform health check and self-healing if needed"""
        try:
            current_time = time.time()
            
            # Check if it's time for health check
            if current_time - self.last_health_check < self.health_check_interval:
                return True
            
            self.last_health_check = current_time
            
            # Check Polymarket API connectivity
            if self.trader and self.trader.client:
                api_healthy = await self.trader.client.health_check()
                
                if not api_healthy:
                    logger.warning("Polymarket API health check failed")
                    await self._heal_connection()
                    return False
                
                logger.debug("Health check passed")
                return True
            else:
                logger.warning("Trader or client not initialized")
                await self._heal_connection()
                return False
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.error_count += 1
            
            if self.error_count >= self.max_errors:
                logger.error(f"Too many errors ({self.error_count}), attempting restart...")
                await self._restart_bot()
            
            return False
    
    async def _heal_connection(self):
        """Attempt to heal connection issues"""
        try:
            logger.info("Attempting to heal connection...")
            
            # Recreate trader if needed
            if self.trader:
                await self.trader.cleanup()
            
            self.trader = Trader()
            logger.info("Connection healed successfully")
            
        except Exception as e:
            logger.error(f"Failed to heal connection: {e}")
    
    async def _restart_bot(self):
        """Restart the bot to recover from errors"""
        try:
            logger.info("Restarting trading bot...")
            
            # Reset error count
            self.error_count = 0
            
            # Cleanup and reinitialize
            if self.trader:
                await self.trader.cleanup()
            
            await asyncio.sleep(self.restart_delay)
            await self.initialize()
            
            logger.info("Bot restarted successfully")
            
        except Exception as e:
            logger.error(f"Failed to restart bot: {e}")
    
    async def run_continuous(self):
        """Run the trading bot continuously - execute trades at each 15-minute market cycle"""
        await self.initialize()
        self.running = True
        
        logger.info("Starting continuous trading mode - trading at each 15-minute market cycle")
        
        while self.running:
            try:
                # Perform health check
                await self.health_check()
                
                # Run trading cycle immediately
                if self.trader:
                    logger.info(f"Starting trading cycle at {datetime.now().strftime('%H:%M:%S')}")
                    await self.trader.run_trading_cycle()
                
                # Wait 15 minutes before next cycle (to match market cycles)
                logger.info("Waiting 15 minutes before next trading cycle...")
                
                # Sleep in small intervals to allow for graceful shutdown
                for _ in range(15 * 60):  # 15 minutes
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.error_count += 1
                
                if self.error_count >= self.max_errors:
                    logger.error("Too many errors, attempting restart...")
                    await self._restart_bot()
                else:
                    # Wait before retrying
                    await asyncio.sleep(60)
    
    async def run_single_cycle(self):
        """Run a single trading cycle for testing"""
        await self.initialize()
        
        try:
            await self.trader.run_trading_cycle()
            
            # Print summary
            summary = self.trader.get_trade_summary()
            logger.info(f"Trading cycle completed. Summary: {summary}")
            
        except Exception as e:
            logger.error(f"Single trading cycle failed: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up trading bot...")
            
            if self.trader:
                await self.trader.cleanup()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Polymarket Trading Bot')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                       help='Run mode: single cycle or continuous')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (simulated trades)')
    
    args = parser.parse_args()
    
    bot = TradingBot()
    
    try:
        if args.mode == 'continuous':
            await bot.run_continuous()
        else:
            await bot.run_single_cycle()
            
    except Exception as e:
        logger.error(f"Bot execution failed: {e}")
        sys.exit(1)
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
