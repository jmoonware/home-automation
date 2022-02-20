from autopool.logic.device import *
from autopool.hardware.OneWire import *

class SimProbe():
	def __init__(self):
		self.device_paths=['Simulated']
	def LogTemperature(self):
		pass

class ThermalDevice(Device):
	def DevInit(self):
		self.theProbe=DS18B20()
	def SimInit(self):
		self.theProbe=SimProbe()
	def LogTemperature(self):
		return(self.theProbe.LogTemperature())
	def __str__(self):
		return("{0},path={1})".format("Thermal:DS18B20",str(self.theProbe.device_paths)))
	def Status(self):
		return(str(self))
	def Shutdown(self):
		self.logger.debug("{0}: Thermal probe shutdown".format(self))
