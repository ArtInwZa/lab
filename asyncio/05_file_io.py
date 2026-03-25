"""
Lesson 05: File I/O

Real-world case: process a batch of log files — read, parse, summarize.

sync  = open file, read, close, repeat for every file
async = read all files at the same time using aiofiles

The bigger the files and the more of them — the bigger the gap.
"""

import asyncio
import os
import time

import aiofiles

LOG_DIR = "/tmp/asyncio_logs"
FILE_COUNT = 10
LINES_PER_FILE = 5_000


# ── Setup — create sample log files ──────────────────────────────────────────

def create_log_files():
    os.makedirs(LOG_DIR, exist_ok=True)
    for i in range(FILE_COUNT):
        path = f"{LOG_DIR}/service_{i}.log"
        with open(path, "w") as file:
            for line in range(LINES_PER_FILE):
                file.write(f"2024-01-01 INFO service_{i} processed request {line}\n")
    print(f"created {FILE_COUNT} log files with {LINES_PER_FILE} lines each\n")


# ── Synchronous ───────────────────────────────────────────────────────────────

def count_lines_sync(path: str) -> int:
    with open(path) as file:
        return sum(1 for _ in file)  # count lines by iterating


def run_sync():
    start = time.perf_counter()

    total_lines = 0
    for i in range(FILE_COUNT):
        path = f"{LOG_DIR}/service_{i}.log"
        count = count_lines_sync(path)  # blocks while reading — OS I/O wait
        total_lines += count

    elapsed = time.perf_counter() - start
    print(f"  total lines: {total_lines:,}")
    print(f"sync total: {elapsed:.3f}s\n")


# ── Asynchronous ─────────────────────────────────────────────────────────────

async def count_lines_async(path: str) -> int:
    # aiofiles reads the file without blocking the event loop
    # other files can be read at the same time
    async with aiofiles.open(path) as file:
        content = await file.read()
        return content.count("\n")


async def run_async():
    start = time.perf_counter()

    # kick off all file reads simultaneously
    tasks = [
        asyncio.create_task(count_lines_async(f"{LOG_DIR}/service_{i}.log"))
        for i in range(FILE_COUNT)
    ]
    counts = await asyncio.gather(*tasks)
    total_lines = sum(counts)

    elapsed = time.perf_counter() - start
    print(f"  total lines: {total_lines:,}")
    print(f"async total: {elapsed:.3f}s")


# ── Main ──────────────────────────────────────────────────────────────────────

create_log_files()

print("=== Synchronous — one file at a time ===")
run_sync()

print("=== Asynchronous — all files at once ===")
asyncio.run(run_async())
