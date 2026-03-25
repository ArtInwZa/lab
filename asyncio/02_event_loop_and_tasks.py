"""
Lesson 02: Event Loop & Tasks

Event loop is the "heart" of asyncio — it's a loop that keeps asking
"is there any task ready to run?" and runs it.

Coroutine vs Task:
- coroutine = just a "definition" that hasn't run yet (like a recipe not yet cooked)
- task      = a coroutine handed to the event loop to manage (food currently being cooked)
"""

import asyncio
import time


# ── Part 1: Coroutine ≠ Calling the function ──────────────────────────────────

async def say_hello():
    print("hello")


async def part1_coroutine_is_not_a_call():
    print("--- Part 1: Coroutine is just an object ---")

    coroutine = say_hello()  # does NOT run yet — just creates a coroutine object
    print(f"type: {type(coroutine)}")  # <class 'coroutine'>

    await coroutine  # this is what actually runs it
    print()


# ── Part 2: Task vs Await ─────────────────────────────────────────────────────

async def job(name: str, seconds: int):
    print(f"  {name} started")
    await asyncio.sleep(seconds)  # yields control — event loop can run other tasks here
    print(f"  {name} done after {seconds}s")
    return f"{name}_result"


async def part2_task_vs_await():
    print("--- Part 2: await (sequential) ---")
    start = time.perf_counter()

    # plain await = block and wait until this finishes before moving on
    # event loop has nothing else to do here — it just waits
    await job("A", 2)
    await job("B", 2)

    print(f"sequential: {time.perf_counter() - start:.1f}s\n")

    print("--- Part 2: create_task (concurrent) ---")
    start = time.perf_counter()

    # create_task() hands the coroutine to the event loop immediately
    # it starts running right away — we don't block here
    task_a = asyncio.create_task(job("A", 2))
    task_b = asyncio.create_task(job("B", 2))

    # now we await the results — while waiting for A, event loop runs B
    result_a = await task_a
    result_b = await task_b  # B is likely already done by the time we get here

    print(f"concurrent: {time.perf_counter() - start:.1f}s")
    print(f"results: {result_a}, {result_b}\n")


# ── Part 3: Exactly when does the event loop switch? ─────────────────────────

async def worker(name: str):
    print(f"  {name}: step 1")
    await asyncio.sleep(0)  # sleep(0) = just yield control, no actual wait — forces a switch
    print(f"  {name}: step 2")
    await asyncio.sleep(0)  # yield again so the other worker gets a turn
    print(f"  {name}: step 3")


async def part3_how_event_loop_switches():
    print("--- Part 3: Event loop switches at every await ---")

    # watch the output — X and Y alternate at every await
    # this proves the event loop switches exactly at await points
    await asyncio.gather(worker("X"), worker("Y"))
    print()


# ── Part 4: Task cancellation ─────────────────────────────────────────────────

async def long_running_job():
    try:
        print("  long job: started")
        await asyncio.sleep(10)  # will be cancelled before this finishes
        print("  long job: done")  # this line will never be reached
    except asyncio.CancelledError:
        print("  long job: cancelled! cleaning up...")
        raise  # must re-raise so the event loop knows the cancellation succeeded


async def part4_cancellation():
    print("--- Part 4: Cancelling a task ---")

    task = asyncio.create_task(long_running_job())
    await asyncio.sleep(1)  # let it run for 1 second, then cancel

    task.cancel()  # sends CancelledError into the task at its current await point

    try:
        await task  # wait for the task to finish handling the cancellation
    except asyncio.CancelledError:
        print("  main: task was cancelled successfully")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    await part1_coroutine_is_not_a_call()
    await part2_task_vs_await()
    await part3_how_event_loop_switches()
    await part4_cancellation()


asyncio.run(main())
