# llm-utils

A tiny shared Python utility module: exponential backoff retry decorator for LLM API calls, and a prompt caching wrapper that prefixes a cached system prompt block. No dependencies beyond the Anthropic/OpenAI SDK. 

## Scoping

System Design Field Guide

1. Problem Statement

Pain: LLM applications across [team/org] face two recurring costs:
1. Network failures cause unhandled request floods when connectivity returns
2. ~X% of user queries are duplicates, resulting in ~Y%/month in unneccessary API spend

Impact: Shared retry/caching utilities eliminate both-reducing API costs by X% and improving reliability across all dependant projects.

2. User Roles + User Journeys

Goal: Name who uses the system and map what they actually do step by step.

This utility would be used by a Backend Developer.
- Wants: Reliable LLM API calls without manual retry logic
- Success: "I decorate my API callm it handles transient failures transparently"

Journey (highlighted as primary value driver):
1. Dev writes an LLM call wrapped in @retry_with_backoff
2. Network timeout occurs on an attempt
3. Decorator retries with exponential backoff
4. Request succeeds on retry
5. Dev's endpoint returns data to user without manual error handling

3. Requirements

Goal: Turn user journeys into a contract the system must honour.

Functional:
- The @retry_with_backoff decorator shall retry failed request with exponential back off
- The priompt caching wrapper shall preprend a cached system prompt without modifying the user input
- Both shall work with Anthropic/OpenAI SDKs (but will also test on Ollama locally)

Non-Functional:
- Retry logic shall not exceed 30 seconds total (max backoff)
- Decorator shall add <5ms overhead on successful requests
- Caching shall be transparent - the wrapper reutrns the same response shape as uncached calls
- Must work with any LLM model/endpoint (no hardcoded assumptions)

4. High-Level Design

Goal: Show the system's moving parts without committing to any specific technology.

User Code
    ↓ 
@retry_with_backoff decorator
    ↓
LLM API call
    ↓
[Success] → return response
[Failure] → exponential backoff → retry

User Code
    ↓ 
@cache_system_prompt wrapper
    ↓ 
Prepend cached block to system message
    ↓ 
LLM API call
    ↓ 
Return response (with cache metadata if needed)


5. Stack Decisions

Decision: Use decorators (not middleware/wrappers/context managers)
Trade-off:
- Pro: Least intrusive, zero code change in calling code
- Con: Limited to function wrapping, can't intercept at network layer
- Why chosen: Matches the use case (LLM calls are functions; minimal migration for users)

Decision: No external dependencies beyond SDK
Trade-off:
- Pro: Zero compatibility headaches, easy to vendor/copy
- Con: Can't use fancy back off libraries (but exponential backoff is trivial anyway)
- Why chosen: Shared utilities should be drop-in; dependencies are friction)

6. API Contract

@retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
def my_llm_call():
    response = client.messages.create(...)
    return response

#### Request: Function decorated, called as normal
#### Response: Same type as underlying LLM SDK returns
#### Raises: Original exception if all retries exhausted
#### Side effect: Logs retry attempts (optional)

@cache_system_prompt(system_prompt="You are a helpful...")
def my_llm_call(user_input):
    response = client.messages.create(
        messages=[{"role": "user", "content": user_input}],
        ...
    )
    return response

#### The wrapper intercepts, prepends the cached prompt, makes call
#### Response: Identical to uncached version
#### Cost: Saves N API calls if N users ask similar things

system prompt cache for now, response caching in future due to vector db requirement.

NOTES OF THINGS TO DO:
6. Build (with unit tests per component)

Goal: Implement the architecture. Tests are not an afterthought — they're part of the definition of done for each component.

The professional rhythm:

Write the function/class signature and docstring first. The interface before the implementation.
Write the unit test for it (what inputs → what outputs, including edge cases).
Implement until the test passes.
Refactor if needed — tests protect you while you do.

What a unit test covers: one function, one behaviour, no real external calls (mock them). Fast enough to run on every save.

Code quality at this stage: names are unambiguous, functions do one thing, error handling is explicit (no silent failures), no magic numbers (use constants with names), comments explain why, not what.

7. Integration Testing

Goal: Test that components work correctly together, especially at the seams.

Unit tests prove each box works in isolation. Integration tests prove the arrows between them work.

What to test:

The full request-to-response path through real (or realistic test-double) components
What happens at the boundary when one component returns something unexpected — bad JSON, empty response, timeout
The batch path end to end: real CSV in, real CSV out, correct shape

Approach: Use a small, fixed dataset with known expected outputs. Your test asserts on the output shape and key values, not on exact LLM-generated strings (those are non-deterministic). Assert on structure and type.

Red flag to avoid: Testing only the happy path. The interesting bugs live at the edges.

8. Code Review (Self-PR)

Goal: Read your own code as if you've never seen it.

Check out your branch, open a PR against main, and review the diff.

Questions to ask line by line:

Would a new engineer understand this in 6 months with no context?
Is error handling consistent across all functions, or patchy?
Are there any places where a failure would be silent?
Is anything hardcoded that should be configurable?
Are there obvious security issues — credentials in code, unsanitised inputs?
Does the README match what the code actually does?

Write comments on your own PR as if they were from a colleague. Merge only when you'd be comfortable if a senior engineer read this cold.

This is a habit. It catches things code-brain misses.

9. Deploy + Observability

Goal: Get it running in a real environment, and know when it's broken before a user tells you.

Deploy checklist:

Config lives in environment variables, not in code
Secrets are not in the repository
The app starts from a clean state (no local state required)
There is a health check endpoint that returns 200 when the service is ready

Observability = logs + metrics + alerts. At minimum:

Logs: every request in, every response out, every error with stack trace. Structured (JSON), not print statements.
Metrics: request count, error rate, latency. Even a simple file or stdout metric is better than nothing.
Alerts: define at least one condition that would wake you up — error rate above X%, or no requests for Y minutes when there should be.

The question to answer: If this pipeline started returning garbage at 2am, how would I know, and how quickly? If the answer is "when someone complained", observability is not done.
