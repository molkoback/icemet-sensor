import datetime
import os

class FileException(Exception):
	pass

class File:
	def __init__(self, sensor_id, dt, frame, empty):
		self.sensor_id = sensor_id
		self.dt = dt
		self.frame = frame
		self.empty = empty
	
	def __repr__(self):
		return "<File %s>" % str(self)
	
	def __str__(self):
		return self.name
	
	def __eq__(self, other):
		return (
			self.sensor_id == other.sensor_id and
			self.dt == other.dt and
			self.frame == other.frame
		)
	
	def __ne__(self, other):
		return not self.__eq__(other)
	
	def __lt__(self, other):
		return (
			(self.sensor_id<other.sensor_id) or
			(self.sensor_id==other.sensor_id and self.dt<other.dt) or
			(self.sensor_id==other.sensor_id and self.dt==other.dt and self.frame<other.frame)
		)
	
	def __le__(self, other):
		return self.__eq__(other) or self.__lt__(other)
	
	def __gt__(self, other):
		return not self.__le__(other)
	
	def __ge__(self, other):
		return not self.__lt__(other)
	
	@property
	def name(self):
		return "%02d_%02d%02d%02d_%02d%02d%02d%03d_%06d_%s" % (
			self.sensor_id%100,
			self.dt.day, self.dt.month, self.dt.year%100,
			self.dt.hour, self.dt.minute, self.dt.second, self.dt.microsecond/1000,
			self.frame%1000000,
			"F" if self.empty else "T"
		)
	
	def path(self, root, ext):
		if not ext or ext[0] == ".":
			raise FileException("Invalid file type")
		return os.path.join(root, self.name + "." + ext)
	
	@classmethod
	def frompath(cls, path):
		try:
			name = path.rsplit(os.sep, 1)[-1].rsplit(".", 1)[0]
			sensor_id = int(name[0:2])
			dt = datetime.datetime(
				int(name[7:9])+2000, int(name[5:7]), int(name[3:5]),
				hour=int(name[10:12]), minute=int(name[12:14]), second=int(name[14:16]),
				microsecond=int(name[16:19])*1000
			)
			frame = int(name[20:26])
			empty = name[27] == "F"
			return cls(sensor_id, dt, frame, empty)
		except:
			raise FileException("Invalid file path")
