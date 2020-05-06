from icemet_sensor.worker import Worker

from icemet.file import File

from ftplib import FTP
import os
import time

class Sender(Worker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, name="SENDER", delay=1.0)
		self._ftp = None
	
	@property
	def _connected(self):
		try:
			self._ftp.voidcmd("NOOP")
			return True
		except:
			return False
	
	def _connect(self):
		try:
			self._ftp = FTP(timeout=5)
			self._ftp.connect(host=self.cfg.ftp.host, port=self.cfg.ftp.port)
			self._ftp.login(user=self.cfg.ftp.user, passwd=self.cfg.ftp.passwd)
			
			if self._connected:
				self.log.debug("Connected to {}:{}".format(self.cfg.ftp.host, self.cfg.ftp.port))
				return True
		except:
			self.log.warning("Couldn't connect to {}:{}".format(self.cfg.ftp.host, self.cfg.ftp.port))
		return False
	
	def _disconnect(self):
		self._ftp.close()
		self.log.debug("Disconnected")
	
	def _send(self, fn_in, fn_out):
		if self._connected or self._connect():
			try:
				with open(fn_in, "rb") as fp:
					self._ftp.storbinary("STOR %s" % fn_out, fp)
				return True
			except:
				pass
		return False
	
	def _find_files(self):
		files = []
		for fn in os.listdir(self.cfg.save.dir):
			path = os.path.join(self.cfg.save.dir, fn)
			if os.path.isfile(path) and fn.rsplit(".", 1)[-1] == self.cfg.save.type:
				try:
					files.append(File.frompath(fn, open_image=False))
				except:
					pass
		files.sort()
		return files
	
	def init(self):
		self.log.info("FTP server {}:{}".format(self.cfg.ftp.host, self.cfg.ftp.port))
		self._connect()
	
	def loop(self):
		for f in self._find_files():
			t = time.time()
			fn_in = f.path(root=self.cfg.save.dir, ext=self.cfg.save.type, subdirs=False)
			fn_out = f.path(root=self.cfg.ftp.path, ext=self.cfg.save.type, subdirs=False)
			if self.quit.get() or not self._send(fn_in, fn_out):
				break
			os.remove(fn_in)
			self.log.debug("Sent {} ({:.2f} s)".format(f.name, time.time()-t))
		return True
	
	def cleanup(self):
		self._disconnect()
