import asyncio
import time


async def task_1():
    print(f"Task 1 started in {time.time()}")
    await asyncio.sleep(2)  # Simulate a 2-second task
    print(f"Task 1 completed in {time.time()}")

async def task_2():
    print(f"Task 2 started in {time.time()}")
    await asyncio.sleep(1)  # Simulate a 1-second task
    print(f"Task 2 completed in {time.time()}")

async def main():
    await asyncio.gather(task_1(), task_2())  # Run both tasks concurrently

asyncio.run(main())