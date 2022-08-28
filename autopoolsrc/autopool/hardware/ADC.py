# ADS1115 board uses Texas Instruments ADS1115 ADC
import RPi.GPIO as GPIO
from smbus2 import SMBus

I2C_BUS = 1
ALERTPIN =  27 # wired to GPIO pin 
# writing to this address talks to all devices
GENERAL_CALL_ADDRESS = 0b0000000
RESET_COMMAND = 0b00000110
# return sampled values are 16 bit, 2's complement, left justified 
# last 4 LSB are zero
#  
# Up to four different device addresses are supported
# Here is how the pins get wired for each address
# 0x48 is the default
#
# ADDR PIN CONNECTION SLAVE ADDRESS
# GND 1001000 0x48 (default)
# VDD 1001001 0x49
# SDA 1001010 0x4A
# SCL 1001011 0x4B
ADS_ADR = 0x48
# From the ADS1015 data sheet
# There are 4 register addresses, which are the 2 LSB's in the
# register address pointer byte  
#
#	Register address pointer
#	00 : Conversion register
#	01 : Config register
#	10 : Lo_thresh register (for comparator function)
#	11 : Hi_thresh register (for comparator function)
P_CONVERSION = 0x0
# write this for next two bytes to address Configuration register
P_CONFIGURATION = 0x1
# min 0x8000
P_LOW_THRESHOLD = 0x2
# max 0x7FF0
P_HIGH_THRESHOLD = 0x3

# config register
# Default value is:
# '0b10000011 10000101'
#    ________ ________
#      LSB      MSB
#
# Config register bits
#
CR_OS=15 # R/W 1h Operational status or single-shot conversion start
#		When writing:
CR_OS_NA =	0 # No effect
CR_OS_START = 1 # Start a single conversion (when in power-down state)
#		When reading:
#			0 : Device is currently performing a conversion
#			1 : Device is not currently performing a conversion
CR_MUX = 12 # [2:0] R/W 0h Input multiplexer configuration (ADS1015 only)
#			Differential:
CR_MUX_0_1=0b000 # AINP = AIN0 and AINN = AIN1 (default)
CR_MUX_0_3=0b001 # AINP = AIN0 and AINN = AIN3
CR_MUX_1_3=0b010 # AINP = AIN1 and AINN = AIN3
CR_MUX_2_3=0b011 # AINP = AIN2 and AINN = AIN3
#			Single Ended:
CR_MUX_0_G=0b100 # AINP = AIN0 and AINN = GND
CR_MUX_1_G=0b101 # AINP = AIN1 and AINN = GND
CR_MUX_2_G=0b110 # AINP = AIN2 and AINN = GND
CR_MUX_3_G=0b111 # AINP = AIN3 and AINN = GND
#
CR_PGA=9 # [2:0] R/W 2h Programmable gain amplifier configuration
CR_PGA_p3=0b000 # FSR = ±6.144 V
CR_PGA_p5=0b001 # FSR = ±4.096 V
CR_PGA_1= 0b010 # FSR = ±2.048 V (default)
CR_PGA_2= 0b011 # FSR = ±1.024 V
CR_PGA_4= 0b100 # FSR = ±0.512 V
CR_PGA_8= 0b101 # FSR = ±0.256 V
#	CR_PGA_8a=0b110 # FSR = ±0.256 V
#	CR_PGA_8b=0b111 # FSR = ±0.256 V
CR_PGA_GAINS={
		0.3:CR_PGA_p3,
		0.5:CR_PGA_p5,
		1:CR_PGA_1,
		2:CR_PGA_2,
		4:CR_PGA_4,
		8:CR_PGA_8
}
#
CR_MODE=8 # R/W 1h	Device operating mode
#		This bit controls the operating mode.
CR_MODE_CONT  =0 # Continuous-conversion mode
CR_MODE_SINGLE=1 # Single-shot mode or power-down state (default)
#
CR_DR=5 # [2:0] R/W 4h Data rate
#		These bits control the data rate setting.
#			000 : 128 SPS
#			001 : 250 SPS
#			010 : 490 SPS
#			011 : 920 SPS
CR_DR_1 = 0b100 # 1600 SPS (default)
#			101 : 2400 SPS
#			110 : 3300 SPS
#			111 : 3300 SPS
CR_COMP_MODE=4 # R/W 0h Comparator mode (ADS1014 and ADS1015 only)
#		This bit configures the comparator operating mode. This bit serves no function on
#		the ADS1013.
CR_COMP_MODE_TRAD   = 0 # Traditional comparator (default)
CR_COMP_MODE_WINDOW = 1 # Window comparator
#
CR_COMP_POL=3 # R/W 0h Comparator polarity (ADS1014 and ADS1015 only)
#		This bit controls the polarity of the ALERT/RDY pin. This bit serves no function on
#		the ADS1013.
CR_COMP_POL_ACTLOW   = 0 # Active low (default)
CR_COMP_POL_ACTHIGH  = 1 # Active high
#
CR_COMP_LAT=2 # R/W 0h Latching comparator (ADS1014 and ADS1015 only)
#		This bit controls whether the ALERT/RDY pin latches after being asserted or
#		clears after conversions are within the margin of the upper and lower threshold
#		values. 
CR_COMP_LAT_NONLATCH = 0 # Nonlatching comparator (default).
CR_COMP_LAT_LATCH    = 1 # Latching comparator. The asserted ALERT/RDY pin remains latched until read
#
CR_COMP_QUE=0 # [1:0] R/W 3h
#		Comparator queue and disable (ADS1014 and ADS1015 only)
CR_COMP_QUE_1       = 0b00 # Assert after one conversion
CR_COMP_QUE_2       = 0b01 # Assert after two conversions
CR_COMP_QUE_4       = 0b10 # Assert after four conversions
CR_COMP_QUE_DISABLE = 0b11 # Disable comparator (default)


class ADS1115():	 
	def __init__(self,settings=None):
		self.addr=ADS_ADR
		self.gain=1
		self.single=False
		self.pos=0
		self.neg=1
		self.mode=CR_MODE_SINGLE
		if settings:
			for k in settings:
				self.__dict__[k]=settings[k]
		if not self.gain in CR_PGA_GAINS.keys():
			raise ValueError("Bad gain value {0}: valid values are {1}".format(self.gain,','.join(['{0:.1f}'.format(x) for x in CR_PGA_GAINS.keys()])))	
		self.max_volts=2.048/self.gain
		self.set_input(single=self.single,pos=self.pos,neg=self.neg,gain=self.gain)
	def set_input(self,single=False,pos=0,neg=1,gain=1,mode=CR_MODE_SINGLE):
		cr=self._config_register(single=single,pos=pos,neg=neg,gain=gain,mode=mode)
		self.single=single
		self.pos=pos
		self.neg=neg
		self.gain=gain
		self.mode=mode
		with SMBus(I2C_BUS) as smb:
			smb.write_word_data(self.addr,P_CONFIGURATION,cr)
	def reset(self):
		with SMBus(I2C_BUS) as smb:
			smb.write_byte(GENERAL_CALL_ADDRESS,RESET_COMMAND)
	def read_voltage(self):
		rv=0xFFFF # out of range
		cr=self._config_register(single=self.single,pos=self.pos,neg=self.neg,gain=self.gain,mode=self.mode)
		with SMBus(I2C_BUS) as smb:
			smb.write_word_data(self.addr,P_CONFIGURATION,cr)
			rv=smb.read_word_data(self.addr,P_CONVERSION)
		# todo: check for range
		volts=(self._2C_to_int(self._swap_endian(rv)))*self.max_volts/(2**15*self.gain)
		return(volts)
	def get_config(self):
		''' Get default config register value '''
		with SMBus(I2C_BUS) as smb:
			v=smb.read_word_data(self.addr,P_CONFIGURATION)
			return(v)
	def _2C_to_int(self,x):
		if x&0x8000: # negative
			ret= -int((x-1)^0xFFFF)
		else:
			ret=int(x)
		return(ret)
	def _swap_endian(self,x):
		LSB=x>>8
		MSB=x<<8
		return((LSB+MSB)&0xFFFF)
	def _config_register(self,os=CR_OS_START,single=False,pos=0,neg=1,gain=1,mode=CR_MODE_SINGLE,data_rate=CR_DR_1,comparator_mode=CR_COMP_MODE_TRAD,comparator_pol=CR_COMP_POL_ACTLOW,comparator_latch=CR_COMP_LAT_NONLATCH,comparator_que=CR_COMP_QUE_DISABLE):
		''' Args: os,single,pos,neg,gain,mode,data_rate,
			comparator_mode,comparator_pol,comparator_latch,
			comparator_que
		'''
		if os==0 or os==1:
			retval=os<<CR_OS
		if single:	
			if pos==0:
				retval+=CR_MUX_0_G<<CR_MUX
			elif pos==1:
				retval+=CR_MUX_1_G<<CR_MUX
			elif pos==2:
				retval+=CR_MUX_2_G<<CR_MUX
			elif pos==3:
				retval+=CR_MUX_3_G<<CR_MUX
			else:
				raise ValueError("ADC: Invalid input channel {0}".format(pos))
		else: # differential
			if pos==0 and neg==1:
				retval+=CR_MUX_0_1<<CR_MUX
			elif pos==0 and neg==3:
				retval+=CR_MUX_0_3<<CR_MUX
			elif pos==1 and neg==3:
				retval+=CR_MUX_1_3<<CR_MUX
			elif pos==2 and neg==3:
				retval+=CR_MUX_2_3<<CR_MUX
			else:
				raise ValueError("ADC: Invalid differential values {0},{1}".format(pos,neg))
		# set gain
		if gain in CR_PGA_GAINS.keys():	
			retval+=CR_PGA_GAINS[gain]<<CR_PGA
		else: # FIXME
			retval+=CR_PGA_1<<CR_PGA
		# set mode (continuous or single-shot)
		retval+=(mode<<CR_MODE)
		# set data rate - currently ignored
		retval+=(CR_DR_1<<CR_DR)
		# set comparator mode
		retval+=(comparator_mode<<CR_COMP_MODE)
	#	retval+=(CR_COMP_MODE_TRAD<<CR_COMP_MODE)
		# set comparator polarity
		retval+=(comparator_pol<<CR_COMP_POL)
	#	retval+=(CR_COMP_POL_ACTLOW<<CR_COMP_POL)
		# set comparator latch
		retval+=(comparator_latch<<CR_COMP_LAT)
	#	retval+=(CR_COMP_LAT_LATCH<<CR_COMP_LAT)
		# set comparator queue
		retval+=(comparator_que<<CR_COMP_QUE)
	#	retval+=(CR_COMP_QUE_DISABLE<<CR_COMP_QUE)
		return(self._swap_endian(retval))

