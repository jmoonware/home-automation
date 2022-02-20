from autopool.logic.device import *
from autopool.hardware.DIO import *

class DIODevice(Device):
	def Init(self):
		self.theRelays=Relays()
	def Status(self):
		msg=[]
		for p in PinsOut:
			msg.append("{0}:{1}".format(p,self.Get(p)))
		self.logger.info("{0}: {1}".format(self,';'.join(msg)))	
		return(True)
	def Shutdown(self):
		GPIO.cleanup()
	def Set(self,pin,value):
		if pin in PinsOut:
			GPIO.output(PinsOut[pin],value)	
		else:
			raise KeyError("{0} is not an output pin".format(pin))
	def Get(self,pin):
		if pin in PinsOut:
			return(GPIO.input(PinsOut[pin]))
		else:
			raise KeyError("{0} is not an output pin".format(pin))
