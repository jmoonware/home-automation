from autopool.logic.command import *
from autopool.hardware.OneWire import DS18B20
import os

class MonitorTemperature(Command):
	def Init(self):
		if 'device_path' in self.__dict__:
			self.device=DS18B20(self.device_path)
		else:
			self.device=DS18B20()
		self.blocking=False
		self.loop_count=-1
		self.loop_interval=1.5
		# make sure process is member of video group or this will fail
		self.vccmd='/opt/vc/bin/vcgencmd measure_temp'
	def Execute(self):
		self.device.LogTemperature()
		# this logs the GPU temperature
		T=-999
		with os.popen(self.vccmd) as p:
			ts=p.readline()
		if ts:
			toks=ts.strip().split('=')
			if len(toks)==2:
				tstr=toks[1].split('\'')[0]
				T=float(tstr)
		self.logger.info("GPU Temp=\t{0:.1f} C\t{1:.1f} F".format(T,9*T/5+32))
