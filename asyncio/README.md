# Asyncio Learning

## How Event Loop Works

```
asyncio.run(main())
│
└─► open event loop
        │
        ▼
   ┌─────────────────────────────────────┐
   │           EVENT LOOP                │
   │                                     │
   │  1. Is there any task ready?        │
   │  2. Run it until hitting await      │
   │  3. Task is waiting → save state    │
   │  4. Move to the next task           │
   │  5. Repeat...                       │
   └─────────────────────────────────────┘
        │
        ▼
   No tasks left → close loop
```

---

## Sequential vs Concurrent

### Sequential — plain `await`

```
timeline ──────────────────────────────────────►

task A  [████████ 2s ████████]
task B                        [████████ 2s ████████]
                                                     total: 4s
```

```python
await job("A", 2)  # wait for A to finish
await job("B", 2)  # then do B
```

Event loop has nothing else to do while waiting for A — it just sits idle.

---

### Concurrent — `create_task` then `await`

```
timeline ──────────────────────────────────────►

task A  [████████ 2s ████████]
task B  [████████ 2s ████████]
                              total: 2s
```

```python
task_a = asyncio.create_task(job("A", 2))  # hand A to event loop
task_b = asyncio.create_task(job("B", 2))  # hand B to event loop too
await task_a  # while waiting for A → event loop runs B
await task_b  # B is already done
```

Event loop has 2 tasks — it switches between them while each is waiting.

---

## What is `await`?

```
async def job(name, seconds):
    print(f"{name} started")
    await asyncio.sleep(seconds)
    #  ↑
    #  tells event loop: "I'm waiting, go do something else"
    #  event loop switches to another task
    #  once the wait is over → resumes from here
    print(f"{name} done")
```

`await` = the point where a task yields control back to the event loop.
Without `await` → event loop never gets a chance to switch.

---

## Coroutine vs Task

```
coroutine = asyncio.sleep(2)
│
│  just a "definition" — not running yet
│  like a recipe that hasn't been cooked
│
▼
task = asyncio.create_task(asyncio.sleep(2))
│
│  handed to event loop — now running
│  like food that's currently being cooked
│
▼
result = await task
│
│  wait here until the task finishes and get the result
```

---

## Files

| File | Topic |
| --- | --- |
| `01_why_async.py` | sync vs async — see the difference clearly |
| `02_event_loop_and_tasks.py` | event loop, coroutine, task, cancellation |
