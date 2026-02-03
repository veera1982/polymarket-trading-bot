import os
import json
from py_clob_client.client import ClobClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize CLOB client
host = "https://clob.polymarket.com"
chain_id = 137  # Polygon mainnet

print("Initializing CLOB client...")
client = ClobClient(host, chain_id=chain_id)

print("\nFetching all markets...")
try:
    markets = client.get_markets()
    print(f"Total markets found: {len(markets)}")
    print(f"Market type: {type(markets)}")
    
    # Markets is a dict, iterate over values
    print("\nSearching for 15-minute crypto markets...")
    fifteen_min_markets = []
    
    for market_id, market in markets.items():
        question = str(market.get('question', '')).lower() if isinstance(market, dict) else str(market).lower()
        print(f"\nMarket ID: {market_id}")
        print(f"Question: {question[:100]}...")
        
        if '15' in question and 'minute' in question:
            crypto_assets = ['btc', 'eth', 'sol', 'xrp']
            if any(asset in question for asset in crypto_assets):
                fifteen_min_markets.append(market)
                print(f"  ✓ FOUND 15-minute crypto market!")
                if isinstance(market, dict):
                    print(f"  Active: {market.get('active')}")
    
    print(f"\n\nTotal 15-minute crypto markets: {len(fifteen_min_markets)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
