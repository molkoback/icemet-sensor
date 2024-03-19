import cv2

def show(img):
	f = 640 / img.mat.shape[1]
	mat = cv2.resize(img.mat, dsize=None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
	cv2.imshow("ICEMET-sensor", mat)
	cv2.waitKey(1)

async def on_image(ctx, img):
	await ctx.loop.run_in_executor(ctx.pool, show, img)
