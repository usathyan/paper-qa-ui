"""
Retry utilities for handling API failures with exponential backoff.

This module provides retry decorators and utilities for handling transient failures,
rate limits, and network issues when calling external APIs.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Optional, Type, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError
)
import httpx

# Configure logging for retry operations
logger = logging.getLogger(__name__)

# Common exception types that should trigger retries
RETRYABLE_EXCEPTIONS = [
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.ProtocolError,
    OSError,  # Network errors
    ConnectionError,  # General connection errors
]

def create_retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_exceptions: Optional[List[Type[Exception]]] = None,
) -> Callable:
    """
    Create a retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retry_exceptions: List of exception types to retry on
    
    Returns:
        Decorator function with retry logic
    """
    if retry_exceptions is None:
        retry_exceptions = RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=base_delay,
                max=max_delay
            ),
            retry=retry_if_exception_type(tuple(retry_exceptions)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Pre-configured retry decorators for common use cases
retry_api_call = create_retry_decorator(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retry_exceptions=RETRYABLE_EXCEPTIONS
)

retry_with_long_backoff = create_retry_decorator(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    retry_exceptions=RETRYABLE_EXCEPTIONS
)

def retry_on_rate_limit(func: Callable) -> Callable:
    """Decorator specifically for handling rate limit errors."""
    try:
        import litellm
        rate_limit_exceptions = [litellm.exceptions.RateLimitError]
    except ImportError:
        rate_limit_exceptions = []
    
    return create_retry_decorator(
        max_attempts=3,
        base_delay=5.0,  # Longer initial delay for rate limits
        max_delay=300.0,  # 5 minutes max delay
        retry_exceptions=rate_limit_exceptions
    )(func)

def retry_on_network_error(func: Callable) -> Callable:
    """Decorator for handling network-related errors."""
    return create_retry_decorator(
        max_attempts=3,
        base_delay=0.5,
        max_delay=10.0,
        retry_exceptions=[
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            OSError,
            ConnectionError
        ]
    )(func)

def retry_on_api_error(func: Callable) -> Callable:
    """Decorator for handling general API errors."""
    try:
        import litellm
        api_exceptions = [
            litellm.exceptions.APIError,
            litellm.exceptions.ServiceUnavailableError,
        ]
    except ImportError:
        api_exceptions = []
    
    return create_retry_decorator(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        retry_exceptions=api_exceptions
    )(func)

def handle_retry_error(error: RetryError, operation_name: str = "operation") -> None:
    """
    Handle retry errors with appropriate logging and error messages.
    
    Args:
        error: The RetryError that occurred
        operation_name: Name of the operation that failed
    """
    logger.error(
        f"Failed to complete {operation_name} after {error.retry_state.attempt_number} attempts. "
        f"Last exception: {error.retry_state.outcome.exception()}"
    )

class SimpleRetry:
    """
    Simple retry utility for manual retry logic.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                if attempt < self.max_attempts:
                    delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
        
        logger.error(f"All {self.max_attempts} attempts failed. Last error: {last_exception}")
        raise last_exception
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                if attempt < self.max_attempts:
                    delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
        
        logger.error(f"All {self.max_attempts} attempts failed. Last error: {last_exception}")
        raise last_exception 