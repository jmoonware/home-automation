from autopool.logic.command import *

class ReadLevel(Command):
	def Init(self):
		if not self.device:
			raise ValueError("Readlevel: device is None")
		self.alarm_low=0.71 # V
		self.alarm_high=0.15 # V
		self.blocking=False
	def Execute(self):
		v=self.device.ReadVoltage()
		perc=(v-self.alarm_low)/(self.alarm_high-self.alarm_low)
		perc=100*max(0,min(1,perc))
		self.logger.info("Level = {0:.0f}% {1:.3f} V".format(perc,v))

