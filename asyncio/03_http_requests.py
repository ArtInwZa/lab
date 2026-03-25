"""
Lesson 03: HTTP Requests

Real-world case: fetch data from multiple APIs at the same time.

sync  = wait for each response before sending the next request
async = fire all requests at once, collect results as they arrive
"""

import asyncio
import time
import urllib.request

import aiohttp

# public APIs that return instantly — we use a slow one to make the wait visible
URLS = [
    "https://httpbin.org/delay/2",  # responds after 2 seconds
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
]


# ── Synchronous ───────────────────────────────────────────────────────────────

def fetch_sync(url: str) -> dict:
    # urllib blocks the entire program until the response arrives
    with urllib.request.urlopen(url) as response:
        return {"url": url, "status": response.status}


def run_sync():
    start = time.perf_counter()

    results = []
    for url in URLS:
        result = fetch_sync(url)  # wait for this to finish before moving to the next
        results.append(result)
        print(f"  [sync] got {result['status']} from {result['url']}")

    print(f"sync total: {time.perf_counter() - start:.1f}s — fetched {len(results)} urls\n")


# ── Asynchronous ─────────────────────────────────────────────────────────────

async def fetch_async(session: aiohttp.ClientSession, url: str) -> dict:
    # aiohttp releases control while waiting for the response
    # so other requests can be in-flight at the same time
    async with session.get(url) as response:
        return {"url": url, "status": response.status}


async def run_async():
    start = time.perf_counter()

    # one shared session for all requests — more efficient than opening a new connection per request
    async with aiohttp.ClientSession() as session:
        # fire all requests at once — no waiting between them
        tasks = [asyncio.create_task(fetch_async(session, url)) for url in URLS]
        results = await asyncio.gather(*tasks)

    for result in results:
        print(f"  [async] got {result['status']} from {result['url']}")

    print(f"async total: {time.perf_counter() - start:.1f}s — fetched {len(results)} urls")


# ── Main ──────────────────────────────────────────────────────────────────────

print("=== Synchronous — one request at a time ===")
run_sync()

print("=== Asynchronous — all requests at once ===")
asyncio.run(run_async())
