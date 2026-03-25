"""
Lesson 06: Producer-Consumer Queue

Real-world case: pipeline where one part generates work and another part processes it.
Example: scraper produces URLs → workers fetch and parse them.

asyncio.Queue is the key — it lets producers and consumers run independently
without one blocking the other.
"""

import asyncio
import random
import time


# ── Producer ──────────────────────────────────────────────────────────────────

async def producer(queue: asyncio.Queue, total_jobs: int):
    """Generates jobs and puts them into the queue."""
    for job_id in range(total_jobs):
        # simulate time to discover/generate a job (e.g. crawling a sitemap)
        await asyncio.sleep(random.uniform(0.1, 0.3))

        job = {"id": job_id, "payload": f"data_{job_id}"}
        await queue.put(job)  # put() waits if queue is full — natural backpressure
        print(f"  [producer] queued job {job_id}  (queue size: {queue.qsize()})")

    print("  [producer] done — no more jobs")


# ── Consumer ──────────────────────────────────────────────────────────────────

async def consumer(name: str, queue: asyncio.Queue, results: list):
    """Pulls jobs from the queue and processes them."""
    while True:
        job = await queue.get()  # waits here if queue is empty — no busy-waiting

        # simulate processing time (e.g. parsing HTML, writing to DB)
        processing_time = random.uniform(0.2, 0.6)
        await asyncio.sleep(processing_time)

        result = {"job_id": job["id"], "processed_by": name, "output": job["payload"].upper()}
        results.append(result)

        print(f"  [{name}] finished job {job['id']} in {processing_time:.2f}s")
        queue.task_done()  # signal that this job is fully processed


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    total_jobs = 10
    worker_count = 3  # try changing this to 1 and see how much slower it gets

    # maxsize limits how many jobs can pile up — prevents producer from running too far ahead
    queue: asyncio.Queue = asyncio.Queue(maxsize=5)
    results: list = []

    start = time.perf_counter()

    # start consumers — they run in background waiting for jobs
    workers = [
        asyncio.create_task(consumer(f"worker-{i}", queue, results))
        for i in range(worker_count)
    ]

    # producer runs until it's pushed all jobs into the queue
    await producer(queue, total_jobs)

    # wait until all jobs in the queue are fully processed
    await queue.join()

    # cancel workers — they're in infinite loops waiting for more jobs
    for worker in workers:
        worker.cancel()
    await asyncio.gather(*workers, return_exceptions=True)  # let them finish cleanly

    elapsed = time.perf_counter() - start
    print(f"\nprocessed {len(results)} jobs with {worker_count} workers in {elapsed:.1f}s")
    print(f"jobs processed by each worker:")
    for i in range(worker_count):
        count = sum(1 for r in results if r["processed_by"] == f"worker-{i}")
        print(f"  worker-{i}: {count} jobs")


asyncio.run(main())
