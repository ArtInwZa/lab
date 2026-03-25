"""
Lesson 08: WebSocket — Real-time Communication

Real-world case: live dashboard, chat, stock ticker, game server.

HTTP = you ask, server answers, connection closes
WebSocket = connection stays open, both sides can send messages anytime

asyncio shines here because a WebSocket server must:
- handle many clients at the same time
- keep each connection alive indefinitely
- broadcast messages to all clients instantly

We simulate a server and client in the same file using asyncio so you
can run this without any external setup.
"""

import asyncio
import random
import time


# ── Simulate WebSocket messages ───────────────────────────────────────────────
# In real code you'd use the `websockets` library — the async pattern is identical.
# server_queue  → messages from server to client
# client_queues → messages from each client to server

server_to_clients: dict[str, asyncio.Queue] = {}
client_to_server: asyncio.Queue = asyncio.Queue()


# ── Server ────────────────────────────────────────────────────────────────────

async def handle_client(client_id: str):
    """Handles a single client connection — runs forever until client disconnects."""
    inbox = asyncio.Queue()
    server_to_clients[client_id] = inbox  # register so broadcaster can reach this client

    print(f"  [server] {client_id} connected")

    try:
        while True:
            # wait for a message to arrive from the broadcaster
            message = await inbox.get()
            # simulate sending over the wire
            await asyncio.sleep(0.01)
            print(f"  [server → {client_id}] sent: {message}")
    except asyncio.CancelledError:
        print(f"  [server] {client_id} disconnected")
        del server_to_clients[client_id]
        raise


async def broadcaster(messages: list[str], interval: float):
    """Broadcasts a stream of messages to all connected clients."""
    for message in messages:
        await asyncio.sleep(interval)

        if not server_to_clients:
            continue

        # push the same message to every connected client simultaneously
        tasks = [queue.put(message) for queue in server_to_clients.values()]
        await asyncio.gather(*tasks)
        print(f"  [broadcaster] pushed '{message}' to {len(server_to_clients)} clients")


# ── Client ────────────────────────────────────────────────────────────────────

async def client(client_id: str, listen_for_seconds: float):
    """Simulates a client that connects, listens, then disconnects."""
    # simulate connection delay — clients join at different times
    await asyncio.sleep(random.uniform(0, 0.5))

    # register with server
    server_to_clients[client_id] = asyncio.Queue()
    print(f"  [client] {client_id} joined")

    start = time.perf_counter()
    received = []

    while time.perf_counter() - start < listen_for_seconds:
        try:
            # wait up to 0.5s for the next message
            async with asyncio.timeout(0.5):
                message = await server_to_clients[client_id].get()
                received.append(message)
        except TimeoutError:
            pass  # no message yet — keep waiting

    # disconnect
    if client_id in server_to_clients:
        del server_to_clients[client_id]

    print(f"  [client] {client_id} disconnected after receiving {len(received)} messages: {received}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    stock_prices = [
        "AAPL $189.50",
        "AAPL $189.80",
        "AAPL $190.10",
        "AAPL $189.90",
        "AAPL $190.50",
        "AAPL $191.00",
    ]

    print("=== WebSocket Simulation ===")
    print("broadcaster pushes stock prices to all connected clients\n")

    # clients connect at different times and listen for different durations
    # broadcaster sends messages every 0.8s
    await asyncio.gather(
        broadcaster(stock_prices, interval=0.8),
        client("dashboard", listen_for_seconds=4.0),
        client("mobile-app", listen_for_seconds=2.5),
        client("alert-bot", listen_for_seconds=5.0),
    )

    print("\ndone — all clients disconnected")


asyncio.run(main())
