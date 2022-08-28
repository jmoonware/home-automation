
from autopool.logic.device import *
from autopool.hardware.ADC import *
import logging

class SimADS1115():
	def __init__(self,settings=None):
		self.logger=logging.getLogger(__name__)
		self.addr=0x48
		self.pos=0
		self.gain=1
		if settings:
			if 'addr' in settings.keys():
				self.addr=settings['addr']
	def read_voltage(self):
		if self.addr==0x48:
			return(-999)
		else:
			raise ValueError("Errno 22")

class ADCDevice(Device):
	def SimInit(self):
		self.logger.debug("Simulated ADC")
		self.theADC=SimADS1115(settings=self.settings)
	def DevInit(self):
		self.theADC=ADS1115(settings=self.settings)
	def DevShutdown(self):
		if 'theADC' in self.__dict__ and self.theADC:
			self.theADC.reset()
	def ReadVoltage(self):
		return(self.theADC.read_voltage())
