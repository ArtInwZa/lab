"""
Lesson 04: Database Queries

Real-world case: load data from multiple tables to build a dashboard.

sync  = query one table, wait, query next table, wait...
async = query all tables at the same time, assemble when all are ready

Note: we simulate DB latency with asyncio.sleep instead of a real DB
      so you can run this without any setup.
"""

import asyncio
import time


# ── Simulate DB queries ───────────────────────────────────────────────────────
# In real code these would use an async driver like asyncpg or databases library.
# The pattern is exactly the same — just swap sleep for an actual query.

async def query_users() -> list[dict]:
    await asyncio.sleep(1)  # simulates a slow DB round-trip
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


async def query_orders() -> list[dict]:
    await asyncio.sleep(1.5)  # this table is heavier — takes longer
    return [{"order_id": 101, "user_id": 1, "total": 250}]


async def query_products() -> list[dict]:
    await asyncio.sleep(0.8)
    return [{"product_id": 1, "name": "Widget", "stock": 42}]


async def query_revenue() -> dict:
    await asyncio.sleep(1.2)
    return {"total": 125_000, "currency": "USD"}


# ── Synchronous ───────────────────────────────────────────────────────────────

def run_sync():
    start = time.perf_counter()

    # each query waits for the previous one to finish
    # total time = sum of all query times
    users    = asyncio.run(query_users())
    orders   = asyncio.run(query_orders())
    products = asyncio.run(query_products())
    revenue  = asyncio.run(query_revenue())

    elapsed = time.perf_counter() - start
    print(f"  users: {len(users)}, orders: {len(orders)}, products: {len(products)}, revenue: {revenue['total']}")
    print(f"sync total: {elapsed:.1f}s\n")


# ── Asynchronous ─────────────────────────────────────────────────────────────

async def run_async():
    start = time.perf_counter()

    # all 4 queries run at the same time
    # total time = slowest single query, not the sum
    users, orders, products, revenue = await asyncio.gather(
        query_users(),
        query_orders(),
        query_products(),
        query_revenue(),
    )

    elapsed = time.perf_counter() - start
    print(f"  users: {len(users)}, orders: {len(orders)}, products: {len(products)}, revenue: {revenue['total']}")
    print(f"async total: {elapsed:.1f}s")


# ── Main ──────────────────────────────────────────────────────────────────────

print("=== Synchronous — queries one by one ===")
run_sync()

print("=== Asynchronous — all queries at once ===")
asyncio.run(run_async())
