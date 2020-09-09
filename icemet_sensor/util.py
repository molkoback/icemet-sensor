import asyncio
import gc

async def collect_garbage(ctx, delay):
	try:
		while not ctx.quit.is_set():
			gc.collect(generation=2)
			await asyncio.sleep(delay)
	except KeyboardInterrupt:
		ctx.quit.set()
