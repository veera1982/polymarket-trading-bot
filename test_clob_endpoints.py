import asyncio
import aiohttp
import json

async def test_endpoints():
    """Test different CLOB API endpoint variations"""
    
    endpoints_to_test = [
        ("https://clob.polymarket.com/markets", "No versioning"),
        ("https://clob.polymarket.com/v1/markets", "With /v1/"),
        ("https://clob.polymarket.com/api/markets", "With /api/"),
        ("https://clob.polymarket.com/health", "Health - no versioning"),
        ("https://clob.polymarket.com/v1/health", "Health - with /v1/"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for url, description in endpoints_to_test:
            try:
                print(f"\nTesting: {description}")
                print(f"URL: {url}")
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response (first 200 chars): {str(data)[:200]}")
                    else:
                        text = await response.text()
                        print(f"Response: {text[:200]}")
            except Exception as e:
                print(f"Error: {str(e)[:100]}")

asyncio.run(test_endpoints())
