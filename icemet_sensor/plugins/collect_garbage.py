import asyncio
import gc

async def collect_garbage(quit, delay):
	try:
		while not quit.is_set():
			gc.collect(generation=2)
			await asyncio.sleep(delay)
	except KeyboardInterrupt:
		quit.set()

async def on_init(ctx):
	ctx.loop.create_task(collect_garbage(ctx.quit, 2.0))
