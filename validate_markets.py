import asyncio
from py_clob_client.client import ClobClient

async def main():
    print("Initializing CLOB client...")
    client = ClobClient("https://clob.polymarket.com")
    
    print("\nFetching all markets...")
    markets = client.get_markets()
    
    # Extract market list from response
    print(f"Response type: {type(markets)}")
    print(f"Response keys: {list(markets.keys()) if isinstance(markets, dict) else 'Not a dict'}")
    
    market_list = markets.get('data', []) if isinstance(markets, dict) else markets
    print(f"\nTotal markets: {len(market_list)}")
    
    # Filter for 15-minute crypto markets
    crypto_assets = ['BTC', 'ETH', 'SOL', 'XRP']
    fifteen_min_markets = []
    
    print("\n" + "="*70)
    print("SEARCHING FOR 15-MINUTE CRYPTO MARKETS")
    print("="*70)
    
    for market in market_list:
        if not isinstance(market, dict):
            continue
            
        question = str(market.get('question', ''))
        question_lower = question.lower()
        
        # Check if it's a 15-minute market
        if '15' in question_lower and 'minute' in question_lower:
            # Check if it contains crypto assets
            for asset in crypto_assets:
                if asset.lower() in question_lower:
                    market_id = market.get('condition_id') or market.get('id') or market.get('market_id')
                    fifteen_min_markets.append({
                        'id': market_id,
                        'question': question,
                        'asset': asset,
                        'active': market.get('active'),
                        'closed': market.get('closed'),
                        'accepting_orders': market.get('accepting_orders')
                    })
                    
                    print(f"\n✓ Found {asset} 15-minute market:")
                    print(f"  Market ID: {market_id}")
                    print(f"  Question: {question}")
                    print(f"  Active: {market.get('active')}")
                    print(f"  Closed: {market.get('closed')}")
                    print(f"  Accepting Orders: {market.get('accepting_orders')}")
                    break
    
    print("\n" + "="*70)
    print(f"SUMMARY: Found {len(fifteen_min_markets)} 15-minute crypto markets")
    print("="*70)
    
    # Validate coverage for each asset
    print("\nAsset Coverage:")
    for asset in crypto_assets:
        asset_markets = [m for m in fifteen_min_markets if m['asset'] == asset]
        status = "✓" if len(asset_markets) > 0 else "✗"
        print(f"  {status} {asset}: {len(asset_markets)} market(s)")
    
    # Save market IDs to file
    if fifteen_min_markets:
        print("\nSaving market IDs to market_ids.txt...")
        with open('market_ids.txt', 'w') as f:
            for m in fifteen_min_markets:
                f.write(f"{m['asset']}: {m['id']}\n")
        print("✓ Market IDs saved!")
    
    return fifteen_min_markets

if __name__ == "__main__":
    markets = asyncio.run(main())
