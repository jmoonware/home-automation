import logging
import autopool
import autopool.app
from autopool.logic.command import *
from autopool.commands.DataLogger import DataWriter
from autopool.devices.WindDevice import WindDevice
from autopool.devices.ThermalDevice import ThermalDevice
from autopool.devices.ADCDevice import ADCDevice
import Adafruit_DHT as dht
import time
import os
import numpy as np
import RPi.GPIO as GPIO
import data_url

autopool.app.start_logging(level=logging.DEBUG,filename='nwindlog.txt')
url=data_url.url

# here are some origin,data pairs

class LogWindValues(Command):
	def Init(self):
		self.wd=WindDevice(settings={'simulated':False})
	def Execute(self):
		vmph=self.wd.ReadWindSpeed()
		angle=self.wd.ReadWindDirection()
		if vmph >=0 and vmph < 100: # filter garbage
			self.data_logger.LogData('wind_vmph',vmph)
		self.data_logger.LogData('wind_angle',angle)


class LogHumidity(Command):
	def Init(self):
		# fixme: make device
		self.hd=dht
	def Execute(self):
		ht=self.hd.read_retry(dht.AM2302,26)
		if ht and len(ht) > 1:
			self.logger.debug("Humidity, Temperature {0}".format(ht))
			if ht[0] >= 0. and ht[0] <= 100.:
				self.data_logger.LogData('outside_T',ht[1])
				self.data_logger.LogData('outside_H',ht[0])
			else:
				self.logger.debug("HT Bad Values {0}".format(ht))
		else:
			self.logger.debug("No data from humidity sensor")


temp_probes={'28-01144c250baa':'air_T'}

class LogTemperatureValues(Command):
	def Init(self):
		self.td=ThermalDevice(settings={'simulated':False})
	def Execute(self):
		time.sleep(1) # KLUDGE
		vals=self.td.LogTemperature()
		for name in vals:
			if name in temp_probes:
				self.data_logger.LogData(temp_probes[name],vals[name])


class LogGPUTemperature(Command):
	def Init(self):
		self.blocking=False
		self.loop_count=-1
		self.loop_interval=60
		# make sure process is member of video group or this will fail
		self.vccmd='/opt/vc/bin/vcgencmd measure_temp'
	def Execute(self):
		# this logs the GPU temperature
		T=-999
		with os.popen(self.vccmd) as p:
			ts=p.readline()
		if ts:
			toks=ts.strip().split('=')
			if len(toks)==2:
				tstr=toks[1].split('\'')[0]
				T=float(tstr)
		self.logger.debug("GPU Temp=\t{0:.1f} C\t{1:.1f} F".format(T,9*T/5+32))
		self.data_logger.LogData("GPU_T",T)

# singleton

class LogLevelValues(Command):
	def Init(self):
		if not self.device:
			raise ValueError("Readlevel: device is None")
		self.alarm_low=0.71 # V
		self.alarm_high=0.15 # V
	def Execute(self):
		vs=[]
		with self.device.sync:
			# throw away first reading!
			v=self.device.ReadVoltage()
			for i in range(3):
				vs.append(self.device.ReadVoltage())
				time.sleep(0.1)
		vs.sort()
		if len(vs) > 2:
			v=vs[1] # take median of 3
			perc=(v-self.alarm_low)/(self.alarm_high-self.alarm_low)
			perc=100*max(0,min(1,perc))
			self.logger.debug("Level = {0:.0f}% {1:.3f} V".format(perc,v))
			self.data_logger.LogData('pool_level',perc)
		else:
			self.logger.warning("LogLevel: missing values")

class LogThermistorValues(Command):
	def Init(self):
		if not self.device:
			raise ValueError("Thermistor: device is None")
		self.R_d=9.83e3 # Ohm at ~70 F
		self.V_d=3.3 # volts
		# Steinhart - Hart Equation 1/T = A+B(LnR)+C(LnR)^3
		self.A = 0.001125308852122
		self.B = 0.000234711863267
		self.C = 0.000000085663516	
		
	def Execute(self):
		vs=[]
		with self.device.sync:
			# turn on Pin 13 to V_d
			GPIO.output(13,1)
			time.sleep(0.1) # let it settle
			# throw away first reading!
			self.device.theADC.pos=1 # read pin 1
			self.device.theADC.gain=0.5 # range +/- 4.096 V
			v=self.device.ReadVoltage()
			for i in range(3):
				vs.append(self.device.ReadVoltage())
				time.sleep(0.1)
			# set back to defaults
			self.device.theADC.pos=0
			self.device.theADC.gain=1
			GPIO.output(13,0)
		vs.sort()
		if len(vs) > 2:
			v=vs[1] # take median of 3
			# get resistance from divider
			r_v=v/self.V_d # voltage ratio
			R=r_v*self.R_d/(1-r_v) # resistance of thermistor
			# apply S-H equation
			# Steinhart - Hart Equation 1/T = A+B(LnR)+C(LnR)^3, Kelvin
			T=(1/(self.A+self.B*np.log(R)+self.C*(np.log(R))**3))-273.15
			self.logger.debug("Thermistor T = {0:.1f} C {1:.3f} V".format(T,v))
			self.data_logger.LogData('pool_T',T)
		else:
			self.logger.warning("LogThermistor: missing values")

# happy-case test
def logSomeData():
	dl=DataWriter(settings={'data_root':'data','data_url':url})
	tc=LogWindValues(settings={'blocking':False,'loop_count':-1,'loop_interval':2,'data_logger':dl})
	tc1=LogTemperatureValues(settings={'blocking':False,'loop_count':-1,'loop_interval':60,'data_logger':dl})

	# two commands below share this device
	theADCDevice=ADCDevice(settings={'simulated':False,'single':True})
	# FIXME: put somewhere else
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(13,GPIO.OUT)
	GPIO.output(13,0)

	tc2=LogLevelValues(settings={'blocking':False,'loop_count':-1,'loop_interval':60,'data_logger':dl,'device':theADCDevice})
	tc2a=LogThermistorValues(settings={'blocking':False,'loop_count':-1,'loop_interval':60,'data_logger':dl,'device':theADCDevice})


	tc3=LogGPUTemperature(settings={'blocking':False,'loop_count':-1,'loop_interval':60,'data_logger':dl})
	tc4=LogHumidity(settings={'blocking':False,'loop_count':-1,'loop_interval':60,'data_logger':dl})
	ctrl=autopool.logic.controller.Controller()
	ctrl.Run()
	ctrl.RunRecipe([dl,tc,tc1,tc2,tc2a,tc3,tc4])
#	ctrl.RunRecipe([dl,tc2a])
	while ctrl.Status()==True:
		time.sleep(1)

logSomeData() # should run forever
