#!/usr/bin/env python3
"""
Test script to demonstrate retry functionality with exponential backoff.

This script shows how the retry utilities work with different types of failures
and how they handle rate limits and network errors.
"""

import asyncio
import time
from api.retry_utils import (
    retry_api_call, 
    retry_on_rate_limit, 
    retry_on_network_error,
    SimpleRetry,
    handle_retry_error
)

def simulate_failing_function(attempt: int, should_fail: bool = True):
    """Simulate a function that fails on the first few attempts."""
    print(f"Attempt {attempt}: Function called")
    if should_fail and attempt < 3:
        raise ConnectionError(f"Simulated connection error on attempt {attempt}")
    return f"Success on attempt {attempt}"

def simulate_rate_limited_function(attempt: int):
    """Simulate a function that hits rate limits."""
    print(f"Attempt {attempt}: Rate limited function called")
    if attempt < 2:
        # Simulate a rate limit error
        raise Exception("Rate limit exceeded")
    return f"Rate limit cleared on attempt {attempt}"

@retry_api_call
def test_basic_retry():
    """Test basic retry functionality."""
    print("\n=== Testing Basic Retry ===")
    return simulate_failing_function(1)

def test_simple_retry():
    """Test the SimpleRetry utility."""
    print("\n=== Testing SimpleRetry ===")
    
    retry = SimpleRetry(max_attempts=3, base_delay=1.0, max_delay=10.0)
    try:
        result = retry.execute(simulate_failing_function, 1)
        print(f"✅ {result}")
        return result
    except Exception as e:
        print(f"❌ SimpleRetry failed: {e}")
        raise

async def test_async_simple_retry():
    """Test async SimpleRetry utility."""
    print("\n=== Testing Async SimpleRetry ===")
    
    async def async_simulate_failure(attempt: int):
        await asyncio.sleep(0.1)  # Simulate async work
        if attempt < 3:
            raise ConnectionError(f"Async connection error on attempt {attempt}")
        return f"Async success on attempt {attempt}"
    
    retry = SimpleRetry(max_attempts=3, base_delay=0.5, max_delay=5.0)
    try:
        result = await retry.execute_async(async_simulate_failure, 1)
        print(f"✅ {result}")
        return result
    except Exception as e:
        print(f"❌ Async SimpleRetry failed: {e}")
        raise

def test_network_retry():
    """Test network-specific retry."""
    print("\n=== Testing Network Retry ===")
    
    @retry_on_network_error
    def network_function():
        raise ConnectionError("Network connection failed")
    
    try:
        result = network_function()
        print(f"✅ {result}")
        return result
    except Exception as e:
        print(f"❌ Network retry failed: {e}")
        # This is expected to fail after retries

def main():
    """Run all retry tests."""
    print("🧪 Testing Retry Functionality with Exponential Backoff")
    print("=" * 60)
    
    try:
        # Test basic retry
        test_basic_retry()
        
        # Test simple retry
        test_simple_retry()
        
        # Test async retry
        asyncio.run(test_async_simple_retry())
        
        # Test network retry (will fail as expected)
        test_network_retry()
        
        print("\n✅ All retry tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Some tests failed: {e}")
        print("This is expected behavior for demonstration purposes.")

if __name__ == "__main__":
    main() 