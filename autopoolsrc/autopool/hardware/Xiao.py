# I2C bus readout of Davis 6410 anemometer hooked up to Seeeduino Xiao SAMD21
# 
import RPi.GPIO as GPIO
from smbus2 import SMBus

I2C_BUS = 1
XIAO_ADR = 0x4C
# 
# I set up 3 register addresses, which are the 3 LSB's in the
# register address pointer byte  
#
#	Register address pointer
#	000 : Wind Direction (deg*10)
#	002 : Wind Speed (mph*10)
#	004 : Exception Count
#
P_WIND_DIRECTION = 0x00
P_WIND_SPEED = 0x02
P_EXCEPTION_COUNT = 0x04

class XIAO_I2C():	 
	def __init__(self,settings=None):
		self.addr=XIAO_ADR
		if settings:
			for k in settings:
				self.__dict__[k]=settings[k]
	def reset(self):
		pass # for now
	def read_wind_direction(self):
		rv=0xFFFF # out of range
		with SMBus(I2C_BUS) as smb:
			rv=smb.read_word_data(self.addr,P_WIND_DIRECTION)&0x7FFF
		# rv = 10*degrees, don't forget to /10
		return(rv/10.)
	def read_wind_speed(self):
		rv=0xFFFF # out of range
		with SMBus(I2C_BUS) as smb:
			rv=smb.read_word_data(self.addr,P_WIND_SPEED)&0x7FFF
		# rv = 10*vmph, don't forget to /10
		return(rv/10.)
