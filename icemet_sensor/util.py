import asyncio
from datetime import datetime, timezone
import gc

def utcnow():
	return datetime.utcnow().replace(tzinfo=timezone.utc)

async def collect_garbage(ctx, delay):
	try:
		while not ctx.quit.is_set():
			gc.collect(generation=2)
			await asyncio.sleep(delay)
	except KeyboardInterrupt:
		ctx.quit.set()
