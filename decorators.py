import functools
import time

"""
@retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
def my_llm_call():
    response = client.messages.create(...)
    return response

Request: Function decorated, called as normal
Response: Same type as underlying LLM SDK returns
Raises: Original exception if all retries exhausted
Side effect: Logs retry attempts (optional)
"""

def retry_with_backoff(max_retries=5, base_delay=1, max_delay=30):
    """Delay the decorated function using exponential backoff
    Should not affect the function call.
    Should not modify the decorated function response.
    Should raise the original exception if all retries exhausted.
    Should log all retry attempts."""
    def decorator_retry_with_back_off(func):
        @functools.wraps(func)
        def wrapper_retry_with_backoff(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    # attempt to run input function
                    response = func(*args, **kwargs)
                    print("Trying operation...")
                    return response
                except Exception as e:
                    attempt +=1
                    if attempt == max_retries:
                        print("Max retries reached. Raising error.")
                        raise e

                    # calculate delay: base_delay * 2^attempt, or use max_delay
                    delay = base_delay * 2**attempt if max_delay > (base_delay * 2**attempt) else max_delay
                    print(f"Attempt {attempt} failed. Waiting {delay} seconds...")
                    time.sleep(delay)
            return response
        return wrapper_retry_with_backoff
    return decorator_retry_with_back_off

"""
@cache_system_prompt(system_prompt="You are a helpful...")
def my_llm_call(user_input):
    response = client.messages.create(
        messages=[{"role": "user", "content": user_input}],
        ...
    )
    return response

The wrapper intercepts, prepends the cached prompt, makes call
Response: Identical to uncached version
Cost: Saves N API calls if N users ask similar things
"""

def cache_system_prompt(func):
    """"""