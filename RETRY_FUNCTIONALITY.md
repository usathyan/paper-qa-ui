# Retry Functionality with Exponential Backoff

This document describes the retry functionality implemented in the PaperQA Discovery system using the popular `tenacity` package for robust error handling and exponential backoff.

## Overview

The retry system provides automatic retry logic with exponential backoff for handling transient failures, rate limits, and network issues when calling external APIs. This improves system reliability and user experience.

## Features

### 🔄 **Exponential Backoff**
- **Base Delay**: Configurable initial delay (default: 1 second)
- **Max Delay**: Maximum delay cap (default: 60 seconds)
- **Backoff Factor**: Exponential increase (default: 2x)
- **Max Attempts**: Configurable retry attempts (default: 3)

### 🎯 **Smart Exception Handling**
- **Network Errors**: Connection timeouts, read timeouts, connection errors
- **API Errors**: Rate limits, service unavailable, general API errors
- **HTTP Errors**: Protocol errors, remote protocol errors
- **System Errors**: OSError, ConnectionError

### 🛠 **Multiple Retry Strategies**
- **Basic Retry**: General purpose retry for all retryable exceptions
- **Rate Limit Retry**: Specialized for rate limit errors with longer delays
- **Network Retry**: Optimized for network-related failures
- **API Retry**: Focused on API-specific errors

## Implementation

### Core Components

#### 1. **Retry Decorators** (`api/retry_utils.py`)

```python
# Basic retry decorator
@retry_api_call
def my_function():
    # Will retry on any retryable exception
    pass

# Rate limit specific retry
@retry_on_rate_limit
def api_call():
    # Will retry specifically on rate limit errors
    pass

# Network error retry
@retry_on_network_error
def network_call():
    # Will retry on network-related errors
    pass
```

#### 2. **SimpleRetry Class**

For manual retry control:

```python
from api.retry_utils import SimpleRetry

# Synchronous retry
retry = SimpleRetry(max_attempts=3, base_delay=1.0, max_delay=30.0)
result = retry.execute(my_function, arg1, arg2)

# Asynchronous retry
result = await retry.execute_async(my_async_function, arg1, arg2)
```

#### 3. **Configuration Options**

```python
# Custom retry decorator
@create_retry_decorator(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    retry_exceptions=[MyCustomException]
)
def custom_function():
    pass
```

### Integration Points

#### 1. **PaperQA Query Processing**
- Automatic retry for LLM API calls
- Handles rate limits from OpenRouter.ai
- Retries on network failures

#### 2. **Paper Loading**
- Retry logic for PDF processing
- Handles file system errors
- Network retries for external document fetching

#### 3. **External API Calls**
- Semantic Scholar API retries
- Crossref API retries
- General web request retries

## Usage Examples

### Basic Usage

```python
from api.retry_utils import retry_api_call

@retry_api_call
def fetch_data_from_api():
    # This function will automatically retry on failures
    response = requests.get("https://api.example.com/data")
    return response.json()
```

### Advanced Usage

```python
from api.retry_utils import SimpleRetry

async def process_documents():
    retry = SimpleRetry(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        backoff_factor=2.0
    )
    
    try:
        result = await retry.execute_async(
            process_document,
            document_path
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process document after retries: {e}")
        raise
```

### Rate Limit Handling

```python
from api.retry_utils import retry_on_rate_limit

@retry_on_rate_limit
def call_rate_limited_api():
    # This will retry with longer delays for rate limits
    response = requests.get("https://api.example.com/rate-limited")
    return response.json()
```

## Configuration

### Environment Variables

The retry system respects these environment variables:

- `OPENROUTER_API_KEY`: For OpenRouter.ai API calls
- `SEMANTIC_SCHOLAR_API_KEY`: For Semantic Scholar API calls
- `CROSSREF_API_KEY`: For Crossref API calls

### Default Settings

```python
# Default retry configuration
DEFAULT_RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "backoff_factor": 2.0
}

# Rate limit specific configuration
RATE_LIMIT_CONFIG = {
    "max_attempts": 3,
    "base_delay": 5.0,  # Longer initial delay
    "max_delay": 300.0,  # 5 minutes max
    "backoff_factor": 2.0
}
```

## Error Handling

### Retryable Exceptions

The system automatically retries on these exception types:

- `httpx.ConnectTimeout`
- `httpx.ReadTimeout`
- `httpx.WriteTimeout`
- `httpx.PoolTimeout`
- `httpx.ConnectError`
- `httpx.RemoteProtocolError`
- `httpx.ProtocolError`
- `litellm.exceptions.RateLimitError`
- `litellm.exceptions.ServiceUnavailableError`
- `litellm.exceptions.APIError`
- `OSError`
- `ConnectionError`

### Non-Retryable Exceptions

These exceptions are NOT retried:

- `ValueError`
- `TypeError`
- `KeyError`
- `IndexError`
- Authentication errors
- Permission errors

## Monitoring and Logging

### Log Levels

- **INFO**: Successful retries and completion
- **WARNING**: Retry attempts and delays
- **ERROR**: Final failures after all retries

### Example Log Output

```
INFO: Attempt 1 failed: ConnectionError: Network timeout
WARNING: Retrying in 1.0 seconds...
INFO: Attempt 2 failed: ConnectionError: Network timeout
WARNING: Retrying in 2.0 seconds...
INFO: Attempt 3 succeeded
```

## Testing

### Test Script

Run the test script to verify retry functionality:

```bash
uv run python test_retry.py
```

### Test Coverage

The test script covers:

1. **Basic Retry**: General retry functionality
2. **SimpleRetry**: Manual retry utility
3. **Async Retry**: Asynchronous retry functionality
4. **Network Retry**: Network-specific retry logic

## Benefits

### 🚀 **Improved Reliability**
- Automatic recovery from transient failures
- Reduced manual intervention
- Better user experience

### ⚡ **Performance Optimization**
- Exponential backoff prevents overwhelming APIs
- Smart retry strategies for different error types
- Configurable delays based on error patterns

### 🔧 **Developer Experience**
- Simple decorator-based API
- Comprehensive logging and monitoring
- Easy configuration and customization

### 📊 **Monitoring and Debugging**
- Detailed retry attempt logging
- Error categorization and handling
- Performance metrics tracking

## Future Enhancements

### Planned Features

1. **Circuit Breaker Pattern**: Prevent cascading failures
2. **Retry Metrics**: Track retry success rates and patterns
3. **Dynamic Backoff**: Adjust delays based on API response patterns
4. **Distributed Retry**: Handle retries across multiple instances
5. **Retry Policies**: Configurable retry strategies per API endpoint

### Configuration Improvements

1. **Per-Endpoint Configuration**: Different retry settings for different APIs
2. **Time-Based Policies**: Different retry strategies based on time of day
3. **Load-Based Policies**: Adjust retry behavior based on system load

## Troubleshooting

### Common Issues

1. **Too Many Retries**: Adjust `max_attempts` or `max_delay`
2. **Slow Recovery**: Reduce `base_delay` or `backoff_factor`
3. **Rate Limit Issues**: Use `retry_on_rate_limit` decorator
4. **Network Issues**: Use `retry_on_network_error` decorator

### Debug Mode

Enable debug logging to see detailed retry information:

```python
import logging
logging.getLogger("api.retry_utils").setLevel(logging.DEBUG)
```

## Conclusion

The retry functionality provides a robust foundation for handling transient failures in the PaperQA Discovery system. With exponential backoff, smart exception handling, and comprehensive logging, the system can gracefully handle API failures and provide a reliable user experience.

The implementation uses industry-standard patterns and the popular `tenacity` library, ensuring maintainability and reliability for production use. 