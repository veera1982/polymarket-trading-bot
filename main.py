#!/usr/bin/env python3
"""
Main entry point for the Polymarket Trading Bot
"""

import asyncio
import sys
import argparse
from trading_bot import main as bot_main

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Polymarket Trading Bot - Automated BTC 15m Market Trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode single                    # Run one trading cycle
  %(prog)s --mode continuous               # Run continuously
  %(prog)s --mode single --test            # Test mode (simulated trades)
  %(prog)s --help                          # Show this help message
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['single', 'continuous'],
        default='single',
        help='Run mode: single cycle or continuous trading (default: single)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with simulated trades (no real money)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (default: .env)'
    )
    
    args = parser.parse_args()
    
    # Set up logging level based on verbose flag
    if args.verbose:
        import os
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Set config file path if provided
    if args.config:
        import os
        os.environ['CONFIG_FILE'] = args.config
    
    print("=" * 60)
    print("🤖 Polymarket Trading Bot")
    print("📈 Automated BTC 15m Market Trading")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Test Mode: {'Yes' if args.test else 'No'}")
    print(f"Verbose: {'Yes' if args.verbose else 'No'}")
    print("=" * 60)
    
    try:
        # Run the bot
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Bot failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
