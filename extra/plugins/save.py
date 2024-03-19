from icemet_sensor.util import tmpfile

from icemet.file import FileStatus
from icemet.pkg import create_package, name2ext

import logging
import os
import time

savers = {}

class Saver:
	def __init__(self, ctx):
		self.ctx = ctx
		
		ext = name2ext(self.ctx.cfg["FILE_TYPE"])
		self._file_is_pkg = bool(ext)
		self._file_ext = ext if ext else "."+self.ctx.cfg["FILE_TYPE"]
		self._pkg = None
		
		if not os.path.exists(self.ctx.cfg["SAVE_PATH"]):
			logging.info("Creating path '{}'".format(self.ctx.cfg["SAVE_PATH"]))
			os.makedirs(self.ctx.cfg["SAVE_PATH"])
		logging.info("Save path '{}'".format(self.ctx.cfg["SAVE_PATH"]))
	
	def _update_package(self, img):
		self._pkg.len += 1
		
		if img.status == FileStatus.NOTEMPTY:
			self._pkg.status = FileStatus.NOTEMPTY
		self._pkg.add_img(img)
		
		if img.frame == self.ctx.cfg["MEAS_LEN"]:
			tmp = os.path.join(self.ctx.cfg["SAVE_PATH"], tmpfile()+self._file_ext)
			dst = os.path.join(self.ctx.cfg["SAVE_PATH"], self._pkg.name()+self._file_ext)
			
			t = time.time()
			self._pkg.save(tmp)
			os.rename(tmp, dst)
			logging.debug("Saved {} ({:.2f} s)".format(self._pkg.name(), time.time()-t))
			self._pkg = None
	
	def _save_image(self, img):
		if img.status == FileStatus.EMPTY:
			return
		
		tmp = os.path.join(self.ctx.cfg["SAVE_PATH"], tmpfile()+self._file_ext)
		dst = os.path.join(self.ctx.cfg["SAVE_PATH"], img.name()+self._file_ext)
		
		t = time.time()
		img.save(tmp)
		os.rename(tmp, dst)
		logging.debug("Saved {} ({:.2f} s)".format(img.name(), time.time()-t))
	
	async def process(self, img):
		if self._file_is_pkg and self._pkg is None:
			self._pkg = create_package(
				self.ctx.cfg["FILE_TYPE"],
				sensor_id=self.ctx.cfg["SENSOR_ID"],
				datetime=img.datetime,
				status=FileStatus.EMPTY,
				len=0,
				fps=self.ctx.cfg["MEAS_FPS"],
				**self.ctx.cfg["FILE_OPT"]
			)
		
		# Save or put in the package
		if self._file_is_pkg:
			task = self._update_package
		else:
			task = self._save_image
		await self.ctx.loop.run_in_executor(self.ctx.pool, task, img)

async def on_init(ctx):
	savers[ctx.args.config] = Saver(ctx)

async def on_image(ctx, img):
	await savers[ctx.args.config].process(img)
