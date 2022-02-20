
from autopool.logic.device import *
from autopool.hardware.Xiao import *
import logging
from random import random

dev_addr=0x4C

class SimXiao():
	def __init__(self,settings=None):
		self.logger=logging.getLogger(__name__)
		self.addr=dev_addr
		if settings:
			if 'addr' in settings.keys():
				self.addr=settings['addr']
	def read_wind_speed(self):
		if self.addr==dev_addr:
			return(60*random())
		else:
			raise ValueError("Errno 22")
	def read_wind_direction(self):
		if self.addr==dev_addr:
			return(360*random())
		else:
			raise ValueError("Errno 22")

class WindDevice(Device):
	def SimInit(self):
		self.logger.debug("Simulated Wind (Xiao) Device")
		self.theXiao=SimXiao(settings=self.settings)
	def DevInit(self):
		self.theXiao=XIAO_I2C(settings=self.settings)
	def DevShutdown(self):
		if 'theXiao' in self.__dict__ and self.theXiao:
			self.theXiao.reset()
	def ReadWindSpeed(self):
		return(self.theXiao.read_wind_speed())
	def ReadWindDirection(self):
		return(self.theXiao.read_wind_direction())
