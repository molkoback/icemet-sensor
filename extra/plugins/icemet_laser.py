from icemet_sensor.laser import lasers, Laser

class ICEMETLaser(Laser):
	def __init__(self):
		pass
	
	async def on(self):
		pass
	
	async def off(self):
		pass
	
	def close(self):
		pass

lasers["icemet"] = ICEMETLaser
