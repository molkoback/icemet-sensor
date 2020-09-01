import asyncio
import gc

async def collect_garbage(delay):
	while True:
		gc.collect(generation=2)
		await asyncio.sleep(delay)
