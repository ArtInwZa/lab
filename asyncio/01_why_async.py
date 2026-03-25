"""
Lesson 01: Why async?

Compare synchronous vs asynchronous — doing 3 tasks that each take 1 second.
"""

import asyncio
import time


# ── Synchronous (normal Python) ──────────────────────────────────────────────

def fetch_sync(name: str, seconds: int) -> str:
    print(f"[sync] {name} started")
    time.sleep(seconds)  # blocks everything — the entire program freezes here until the wait is over
    print(f"[sync] {name} done")
    return name


def run_sync():
    start = time.perf_counter()

    # each call must finish before the next one starts
    fetch_sync("task A", 1)
    fetch_sync("task B", 1)
    fetch_sync("task C", 1)

    elapsed = time.perf_counter() - start
    print(f"sync total: {elapsed:.1f}s\n")


# ── Asynchronous ─────────────────────────────────────────────────────────────

async def fetch_async(name: str, seconds: int) -> str:
    print(f"[async] {name} started")
    await asyncio.sleep(seconds)  # yields control back to event loop — other tasks can run while waiting
    print(f"[async] {name} done")
    return name


async def run_async():
    start = time.perf_counter()

    # gather() starts all three tasks at the same time and waits for all of them to finish
    # event loop switches between tasks whenever one is waiting
    await asyncio.gather(
        fetch_async("task A", 1),
        fetch_async("task B", 1),
        fetch_async("task C", 1),
    )

    elapsed = time.perf_counter() - start
    print(f"async total: {elapsed:.1f}s")


# ── Main ─────────────────────────────────────────────────────────────────────

print("=== Synchronous ===")
run_sync()  # runs normally, no event loop needed

print("=== Asynchronous ===")
asyncio.run(run_async())  # opens event loop, runs run_async(), then closes loop
