"""
Lesson 07: Timeout & Retry

Real-world case: calling an unreliable external API.
- Some requests are slow → need timeout
- Some requests fail → need retry with backoff

Without these patterns, one slow/failing API call can hang your entire program.
"""

import asyncio
import random
import time


# ── Simulate an unreliable API ────────────────────────────────────────────────

async def unreliable_api(request_id: int) -> str:
    roll = random.random()

    if roll < 0.3:
        # 30% chance: takes too long
        await asyncio.sleep(5)
        return f"request_{request_id}_slow_result"
    elif roll < 0.5:
        # 20% chance: raises an error
        raise ConnectionError(f"request {request_id}: connection refused")
    else:
        # 50% chance: succeeds quickly
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return f"request_{request_id}_result"


# ── Pattern 1: Timeout ────────────────────────────────────────────────────────

async def fetch_with_timeout(request_id: int, timeout_seconds: float) -> str | None:
    try:
        # asyncio.timeout() cancels the task if it takes longer than the limit
        async with asyncio.timeout(timeout_seconds):
            result = await unreliable_api(request_id)
            return result
    except TimeoutError:
        print(f"  [timeout] request {request_id} exceeded {timeout_seconds}s — giving up")
        return None


# ── Pattern 2: Retry with exponential backoff ─────────────────────────────────

async def fetch_with_retry(request_id: int, max_attempts: int = 3) -> str | None:
    for attempt in range(1, max_attempts + 1):
        try:
            async with asyncio.timeout(1.0):  # timeout per attempt
                result = await unreliable_api(request_id)
                print(f"  [retry] request {request_id} succeeded on attempt {attempt}")
                return result

        except TimeoutError:
            reason = "timed out"
        except ConnectionError as error:
            reason = str(error)

        if attempt < max_attempts:
            # exponential backoff: wait longer between each retry
            # attempt 1 → wait 0.2s, attempt 2 → wait 0.4s, attempt 3 → wait 0.8s
            wait = 0.2 * (2 ** (attempt - 1))
            print(f"  [retry] request {request_id} {reason} — retry {attempt}/{max_attempts - 1} in {wait:.1f}s")
            await asyncio.sleep(wait)
        else:
            print(f"  [retry] request {request_id} failed after {max_attempts} attempts — giving up")

    return None


# ── Pattern 3: Gather with mixed success ──────────────────────────────────────

async def fetch_all_with_timeout(request_ids: list[int]) -> list:
    # return_exceptions=True means gather won't stop if one task fails
    # each result is either the return value or an exception object
    tasks = [fetch_with_timeout(request_id, timeout_seconds=1.0) for request_id in request_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if isinstance(r, str)]
    failures  = [r for r in results if not isinstance(r, str)]
    return successes, failures


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    random.seed(42)  # fixed seed so results are reproducible

    print("=== Pattern 1: Timeout ===")
    start = time.perf_counter()
    results = await asyncio.gather(*[fetch_with_timeout(i, timeout_seconds=1.0) for i in range(5)])
    print(f"results: {results}")
    print(f"time: {time.perf_counter() - start:.1f}s\n")

    print("=== Pattern 2: Retry with backoff ===")
    random.seed(99)
    start = time.perf_counter()
    results = await asyncio.gather(*[fetch_with_retry(i, max_attempts=3) for i in range(5)])
    print(f"results: {results}")
    print(f"time: {time.perf_counter() - start:.1f}s\n")

    print("=== Pattern 3: Gather — partial success is fine ===")
    random.seed(7)
    start = time.perf_counter()
    successes, failures = await fetch_all_with_timeout(list(range(8)))
    print(f"succeeded: {len(successes)}, failed/timed out: {len(failures)}")
    print(f"time: {time.perf_counter() - start:.1f}s")


asyncio.run(main())
