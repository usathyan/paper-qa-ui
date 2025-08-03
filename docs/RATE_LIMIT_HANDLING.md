# Rate Limit Handling in Paper-QA

Paper-QA has sophisticated built-in mechanisms for handling rate limits and API failures. This document explains how these work and how to configure them.

## Built-in Retry Mechanisms

### 1. **Tenacity Integration**
Paper-QA uses the `tenacity` library for robust retry logic with exponential backoff:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
```

### 2. **HTTP Status Code Handling**
Paper-QA specifically handles:
- **403 Forbidden** errors from Semantic Scholar API
- **429 Too Many Requests** (rate limiting)
- **500 Internal Server Error**
- **502 Bad Gateway**
- **503 Service Unavailable**
- **504 Gateway Timeout**

### 3. **Async Retrying**
Paper-QA uses `tenacity.AsyncRetrying` for asynchronous operations, ensuring non-blocking retry behavior.

## Configuration Options

### Environment Variables

You can control API timeouts and retry behavior through environment variables:

```bash
# Semantic Scholar (most commonly rate-limited)
SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT=30.0

# Crossref
CROSSREF_API_REQUEST_TIMEOUT=30.0
CROSSREF_MAILTO=your_email@example.com

# OpenAlex
OPENALEX_API_REQUEST_TIMEOUT=30.0
OPENALEX_MAILTO=your_email@example.com

# Unpaywall
UNPAYWALL_TIMEOUT=30.0
UNPAYWALL_EMAIL=your_email@example.com
```

### Configuration Files

Our configuration files are optimized for rate limit handling:

#### `configs/public_only.json`
```json
{
  "agent": {
    "timeout": 600.0,
    "concurrency": 2,
    "search_count": 8
  },
  "answer": {
    "max_concurrent_requests": 2
  }
}
```

#### `configs/default.json`
```json
{
  "agent": {
    "timeout": 600.0,
    "concurrency": 3,
    "search_count": 20
  },
  "answer": {
    "max_concurrent_requests": 3
  }
}
```

## Rate Limit Strategies

### 1. **Reduced Concurrency**
- Lower `concurrency` values (2-3 instead of 5)
- Lower `max_concurrent_requests` values
- This spreads requests over time

### 2. **Increased Timeouts**
- Higher timeout values (30+ seconds)
- Allows for rate limit recovery periods
- Handles slow API responses

### 3. **Exponential Backoff**
- Starts with 4-second delay
- Increases exponentially up to 10 seconds
- Maximum 3 retry attempts

### 4. **Email Addresses**
- Adding email addresses to API calls
- Improves rate limits for Semantic Scholar, Crossref, etc.
- More respectful API usage

## Testing Rate Limit Handling

Use our test script to verify rate limit handling:

```bash
# Test rate limit handling
make test-rate-limits

# Or run directly
python scripts/test_rate_limits.py
```

## Monitoring Rate Limits

### 1. **Log Analysis**
Look for these patterns in logs:
```
INFO: Retrying request due to 403 Forbidden
INFO: Exponential backoff delay: 4 seconds
INFO: Request successful after 2 retries
```

### 2. **Response Times**
Monitor response times to detect rate limiting:
- Normal: 1-5 seconds
- Rate limited: 10-30 seconds
- Failed: Immediate error

### 3. **Success Rates**
Track success rates across different configurations:
- `public_only`: Lower concurrency, better for rate limits
- `default`: Higher concurrency, faster but more likely to hit limits

## Best Practices

### 1. **Use Appropriate Configurations**
- **Local papers only**: Use `local_only` config
- **Public sources**: Use `public_only` config
- **Combined**: Use `combined` config

### 2. **Set Environment Variables**
```bash
# Copy template
cp env.template .env

# Edit with your values
nano .env
```

### 3. **Monitor and Adjust**
- Start with conservative settings
- Monitor success rates
- Adjust timeouts and concurrency as needed

### 4. **Use Email Addresses**
- Add your email to API calls
- Improves rate limits significantly
- More respectful API usage

## Troubleshooting

### Common Issues

1. **Still hitting rate limits?**
   - Increase timeout values
   - Reduce concurrency further
   - Add email addresses

2. **Slow performance?**
   - Increase concurrency slightly
   - Reduce timeouts
   - Monitor for optimal balance

3. **403 Forbidden errors?**
   - Paper-QA handles these automatically
   - Check if you need an API key
   - Verify email addresses are set

### Debug Mode

Enable debug logging to see retry behavior:

```bash
# Set verbosity to 3
export PQA_VERBOSITY=3

# Run with debug output
python scripts/paper_qa_cli.py --question "Your question" --method public
```

## API-Specific Notes

### Semantic Scholar
- **Rate limit**: 100 requests per 5 minutes (without API key)
- **With API key**: 1000 requests per 5 minutes
- **Email**: Significantly improves limits

### Crossref
- **Rate limit**: 500 requests per day (without email)
- **With email**: 1000 requests per day
- **Polite pool**: Better rate limits with email

### OpenAlex
- **Rate limit**: 100,000 requests per day
- **Email**: Required for better limits
- **Generally very generous**

### Unpaywall
- **Rate limit**: 100,000 requests per day
- **Email**: Required for better limits
- **Very generous limits**

## Summary

Paper-QA's built-in rate limit handling is comprehensive and robust:

✅ **Automatic retry with exponential backoff**  
✅ **HTTP status code specific handling**  
✅ **Configurable timeouts and concurrency**  
✅ **Environment variable configuration**  
✅ **Email-based rate limit improvements**  
✅ **Async non-blocking retry logic**  

The system is designed to handle rate limits gracefully while maintaining good performance. Start with the provided configurations and adjust based on your specific usage patterns. 