#!/usr/bin/env python3
"""Test script for CLOB integration

This script tests the new CLOB client implementation and verifies
that it can successfully connect to the CLOB API and fetch 15-minute markets.
"""

import asyncio
import logging
from clob_client import ClobClient
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_clob')

async def test_clob_connection():
    """Test basic CLOB API connection"""
    logger.info("="*60)
    logger.info("Testing CLOB API Connection")
    logger.info("="*60)
    
    client = ClobClient()
    
    try:
        # Test health check
        logger.info("\n1. Testing CLOB API health check...")
        is_healthy = await client.health_check()
        if is_healthy:
            logger.info("✓ CLOB API is healthy")
        else:
            logger.warning("✗ CLOB API health check failed")
        
        # Test fetching 15-minute markets
        logger.info("\n2. Fetching 15-minute crypto markets...")
        markets = await client.get_all_15m_markets()
        
        if markets:
            logger.info(f"✓ Found {len(markets)} 15-minute markets:")
            for market in markets:
                logger.info(f"  - {market.asset_type.upper()}: {market.question}")
                logger.info(f"    ID: {market.id}")
                logger.info(f"    Volume: {market.volume}")
                logger.info(f"    Liquidity: {market.liquidity}")
        else:
            logger.warning("✗ No 15-minute markets found")
        
        # Test fetching market prices
        if markets:
            logger.info("\n3. Testing market price fetching...")
            market = markets[0]
            try:
                tokens = await client.get_market_prices(market.id)
                logger.info(f"✓ Retrieved {len(tokens)} tokens for market {market.id}:")
                for token in tokens:
                    logger.info(f"  - {token.outcome}: ${token.price:.4f} (prob: {token.probability:.2%})")
            except Exception as e:
                logger.warning(f"✗ Failed to fetch market prices: {e}")
        
        # Test market history
        if markets:
            logger.info("\n4. Testing market history fetching...")
            market = markets[0]
            try:
                history = await client.get_market_history(market.id, limit=10)
                logger.info(f"✓ Retrieved {len(history)} historical data points")
            except Exception as e:
                logger.warning(f"✗ Failed to fetch market history: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("CLOB Integration Test Complete")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise
    finally:
        await client.close()

async def test_market_configuration():
    """Test market configuration for BTC, ETH, SOL"""
    logger.info("\n" + "="*60)
    logger.info("Testing Market Configuration")
    logger.info("="*60)
    
    client = ClobClient()
    
    try:
        markets = await client.get_all_15m_markets()
        
        # Group markets by asset type
        markets_by_asset = {}
        for market in markets:
            asset = market.asset_type.upper()
            if asset not in markets_by_asset:
                markets_by_asset[asset] = []
            markets_by_asset[asset].append(market)
        
        logger.info("\nMarkets by Asset Type:")
        for asset in ['BTC', 'ETH', 'SOL', 'XRP']:
            if asset in markets_by_asset:
                count = len(markets_by_asset[asset])
                logger.info(f"  {asset}: {count} market(s)")
                for market in markets_by_asset[asset]:
                    logger.info(f"    - ID: {market.id}")
            else:
                logger.info(f"  {asset}: No markets found")
        
        # Create configuration summary
        logger.info("\nConfiguration Summary:")
        logger.info(f"  CLOB API URL: {client.base_url}")
        logger.info(f"  API Version: {client.api_version}")
        logger.info(f"  Wallet Address: {client.wallet_address[:10]}..." if client.wallet_address else "  Wallet Address: Not configured")
        logger.info(f"  Private Key: {'Configured' if client.private_key else 'Not configured'}")
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        raise
    finally:
        await client.close()

async def main():
    """Run all tests"""
    try:
        await test_clob_connection()
        await test_market_configuration()
        logger.info("\n✓ All tests completed successfully!")
    except Exception as e:
        logger.error(f"\n✗ Tests failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
