from icemet.file import File
from icemet.worker import Worker

from ftplib import FTP
import os

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
				self.log.debug("Connected to %s:%d" % (self.cfg.ftp.host, self.cfg.ftp.port))
				return True
		except:
			self.log.warning("Couldn't connect to %s:%d" % (self.cfg.ftp.host, self.cfg.ftp.port))
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
	
	def _findFiles(self):
		files = []
		for fn in os.listdir(self.cfg.save.path):
			path = os.path.join(self.cfg.save.path, fn)
			if os.path.isfile(path) and fn.rsplit(".", 1)[-1] == self.cfg.save.type:
				try:
					files.append(File.frompath(fn))
				except:
					pass
		files.sort()
		return files
	
	def init(self):
		self.log.info("FTP server %s:%d" % (self.cfg.ftp.host, self.cfg.ftp.port))
		self._connect()
	
	def loop(self):
		for f in self._findFiles():
			fn_in = f.path(self.cfg.save.path, self.cfg.save.type)
			fn_out = f.path(self.cfg.ftp.path, self.cfg.save.type)
			if self.quit.get() or not self._send(fn_in, fn_out):
				break
			os.remove(fn_in)
			self.log.debug("SENT %s" % f)
		return True
	
	def cleanup(self):
		self._disconnect()
