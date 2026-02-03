import asyncio
from py_clob_client.client import ClobClient

async def main():
    print("Initializing CLOB client...")
    client = ClobClient("https://clob.polymarket.com")
    
    print("\nFetching all markets...")
    markets = client.get_markets()
    
    market_list = markets.get('data', []) if isinstance(markets, dict) else markets
    print(f"Total markets: {len(market_list)}")
    
    # Search for any crypto-related markets
    crypto_assets = ['BTC', 'ETH', 'SOL', 'XRP', 'bitcoin', 'ethereum', 'solana', 'crypto']
    crypto_markets = []
    
    print("\nSearching for ANY crypto-related markets...\n")
    
    for market in market_list[:100]:  # Check first 100
        if not isinstance(market, dict):
            continue
            
        question = str(market.get('question', '')).lower()
        
        for asset in crypto_assets:
            if asset.lower() in question:
                market_id = market.get('condition_id') or market.get('id')
                crypto_markets.append({
                    'id': market_id,
                    'question': market.get('question'),
                    'active': market.get('active'),
                    'closed': market.get('closed')
                })
                print(f"Found: {market.get('question')[:80]}...")
                print(f"  ID: {market_id}, Active: {market.get('active')}, Closed: {market.get('closed')}")
                print()
                break
    
    print(f"\nTotal crypto markets found (first 100): {len(crypto_markets)}")

if __name__ == "__main__":
    asyncio.run(main())
