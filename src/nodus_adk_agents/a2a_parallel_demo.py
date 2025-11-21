"""
A2A Parallel Execution Demo
Demonstrates calling multiple A2A agents concurrently
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import structlog

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from a2a_client import A2AClient

logger = structlog.get_logger()


async def parallel_execution_demo():
    """
    Demo: Execute multiple A2A agent calls in parallel
    
    Scenario: Get weather forecast + currency exchange rate simultaneously
    """
    logger.info("Starting A2A Parallel Execution Demo")
    
    # Create A2A clients for both agents
    weather_client = A2AClient("http://localhost:8001/a2a")
    currency_client = A2AClient("http://localhost:8002/a2a")
    
    # Discover agent capabilities
    logger.info("Discovering agent capabilities...")
    weather_card = await weather_client.discover()
    currency_card = await currency_client.discover()
    
    print("\n📊 Agents Discovered:")
    print(f"  • {weather_card['name']}: {weather_card['description']}")
    print(f"  • {currency_card['name']}: {currency_card['description']}")
    
    # Execute calls in parallel
    print("\n🚀 Executing parallel calls...")
    start_time = datetime.now()
    
    # Launch both requests concurrently
    weather_task = weather_client.call(
        method="get_forecast",
        params={"city": "barcelona", "days": 1}
    )
    
    currency_task = currency_client.call(
        method="convert",
        params={"from_currency": "EUR", "to_currency": "USD", "amount": 100}
    )
    
    # Wait for both to complete
    weather_result, currency_result = await asyncio.gather(
        weather_task,
        currency_task,
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Display results
    print("\n✅ Results received:")
    print(f"\n🌤️  Weather in {weather_result['city'].title()}:")
    forecast = weather_result['forecasts'][0]
    print(f"   Date: {forecast['date']}")
    print(f"   Temperature: {forecast['temp_min']}°C - {forecast['temp_max']}°C")
    print(f"   Condition: {forecast['condition']}")
    print(f"   Precipitation: {forecast['precipitation_prob']}%")
    print(f"   Wind: {forecast['wind_speed']} km/h")
    
    print(f"\n💱 Currency Conversion:")
    print(f"   {currency_result['amount']} {currency_result['from_currency']} = {currency_result['converted_amount']:.2f} {currency_result['to_currency']}")
    print(f"   Exchange Rate: 1 {currency_result['from_currency']} = {currency_result['rate']:.4f} {currency_result['to_currency']}")
    print(f"   Date: {currency_result['date']}")
    
    print(f"\n⏱️  Total execution time: {duration:.2f}s (parallel)")
    
    # Compare with sequential execution
    print("\n📊 Comparing with sequential execution...")
    start_seq = datetime.now()
    
    await weather_client.call(
        method="get_forecast",
        params={"city": "barcelona", "days": 1}
    )
    await currency_client.call(
        method="convert",
        params={"from_currency": "EUR", "to_currency": "USD", "amount": 100}
    )
    
    end_seq = datetime.now()
    duration_seq = (end_seq - start_seq).total_seconds()
    
    speedup = duration_seq / duration
    print(f"   Sequential time: {duration_seq:.2f}s")
    print(f"   Parallel time: {duration:.2f}s")
    print(f"   Speedup: {speedup:.2f}x faster! 🚀")
    
    logger.info("Demo completed successfully")


async def multi_currency_demo():
    """
    Demo: Convert to multiple currencies in parallel
    """
    print("\n" + "="*60)
    print("💱 Multi-Currency Conversion Demo")
    print("="*60)
    
    currency_client = A2AClient("http://localhost:8002/a2a")
    
    # Convert 1000 EUR to multiple currencies
    result = await currency_client.call(
        method="convert_multiple",
        params={
            "from_currency": "EUR",
            "to_currencies": ["USD", "GBP", "JPY", "CHF"],
            "amount": 1000
        }
    )
    
    print(f"\n💰 Converting {result['amount']} {result['from_currency']}:")
    for conversion in result['conversions']:
        print(f"   → {conversion['converted_amount']:,.2f} {conversion['to_currency']} (rate: {conversion['rate']:.4f})")
    
    print(f"\n📅 Date: {result['date']}")


async def weather_multiple_cities_demo():
    """
    Demo: Get weather for multiple cities in parallel
    """
    print("\n" + "="*60)
    print("🌍 Multi-City Weather Demo")
    print("="*60)
    
    weather_client = A2AClient("http://localhost:8001/a2a")
    
    cities = ["barcelona", "madrid", "valencia"]
    
    print(f"\n🌤️  Fetching weather for {len(cities)} cities in parallel...")
    start_time = datetime.now()
    
    # Launch all requests concurrently
    tasks = [
        weather_client.call(
            method="get_forecast",
            params={"city": city, "days": 1}
        )
        for city in cities
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    for result in results:
        forecast = result['forecasts'][0]
        print(f"\n   {result['city'].title()}:")
        print(f"     • {forecast['temp_min']}°C - {forecast['temp_max']}°C")
        print(f"     • {forecast['condition']}")
    
    print(f"\n⏱️  Fetched {len(cities)} cities in {duration:.2f}s")


async def main():
    """Run all demos"""
    try:
        # Main parallel execution demo
        await parallel_execution_demo()
        
        # Multi-currency demo
        await multi_currency_demo()
        
        # Multi-city weather demo
        await weather_multiple_cities_demo()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {e}")
        print("\n💡 Make sure both agents are running:")
        print("   • Weather Agent: http://localhost:8001")
        print("   • Currency Agent: http://localhost:8002")


if __name__ == "__main__":
    asyncio.run(main())

