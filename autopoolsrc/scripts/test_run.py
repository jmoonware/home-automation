import logging
import autopool
import autopool.app
from autopool.logic.command import *
from autopool.commands.DataLogger import DataWriter
from autopool.commands.DataLogger import DataReader
#from autopool.devices.WindDevice import WindDevice
#from autopool.devices.ThermalDevice import ThermalDevice
#from autopool.devices.ADCDevice import ADCDevice
#import Adafruit_DHT as dht
import time
from datetime import datetime as dt
import pytz
import os
import numpy as np
import requests
import re
#import RPi.GPIO as GPIO

autopool.app.start_logging(level=logging.DEBUG,filename='testlog.txt')
#url='http://ec2-13-59-78-131.us-east-2.compute.amazonaws.com:8084/sensors'
#url='http://ec2-18-188-87-22.us-east-2.compute.amazonaws.com:8084/sensors'
url='http://localhost:8050/sensors'

origin_hourly = 'precip_inphr'
origin_daily = 'precip_inpday'

class LogWebStuff(Command):
	def Init(self):
		self.blocking=False
		self.loop_count=-1
		self.loop_interval=30
		# make sure process is member of video group or this will fail
		self.hourly_precip_url='https://www.weather.gov/source/sgx/hydro/LAXRRMSAN'
		self.daily_precip_url='https://www.wrh.noaa.gov/sgx/obs/rtp/rtp_SGX_23'
		self.station='RNBC1' # Rancho Bernardo
		self.tpat='PERIODS ENDING AT[ ]+([0-9]+)[ ]+([AP]M)'
		# in-mem cache of latest values to avoid multiple logging problem
		self.daily_data={}
		self.hourly_data={}
		if self.data_reader:
			self.daily_data = self.data_reader.GetLatestReadings(origin=origin_daily)
			self.hourly_data = self.data_reader.GetLatestReadings(origin=origin_hourly)
			self.logger.debug("=== init daily " + str(self.daily_data))
			self.logger.debug("=== init hourly " + str(self.hourly_data))
	def Execute(self):
		r=None
		with requests.Session() as req:
			r = req.get(self.hourly_precip_url)

		precip_1hr = 0
		utc_log_timestamp=0
		if r:
			for line in r.text.split('\n'):
				# search for time pattern
				sr=re.search(self.tpat, line.upper())
				if sr and len(sr.groups())==2:
					self.logger.debug("*** " + sr.groups()[0] + sr.groups()[1])
					log_hour=int(sr.groups()[0])
					if sr.groups()[1]=='PM':
						log_hour+=12
					local_now = dt.now()
					utc_log_timestamp = dt(
						year=local_now.year,
						month=local_now.month,
						day=local_now.day,
						hour=log_hour).astimezone(pytz.UTC).timestamp()
				if self.station in line and len(line) > 38:
					station_check = line[0:5].strip()
					station_name = line[6:27].strip()
					elev = line[28:32].strip()
					precip_1hr = float(line[33:38].strip().replace('T','0'))
					self.logger.debug("=".join([station_check,station_name,elev,str(precip_1hr)]))
		self.logger.debug("One hour precip={0} in/hr for {1}".format(precip_1hr,self.station))
		reading=self.data_reader.GetLatestReadings(origin_hourly)
#		self.logger.debug(str(self.data_reader.GetLatestReadings()))
		if len(reading)==0: # no reading
			self.logger.debug("No readings - log {0},{1}".format(utc_log_timestamp,precip_1hr))
			self.data_logger.LogData(origin_hourly,precip_1hr,timestamp=utc_log_timestamp)
			# KLUDGE: wait for data_logger to get data on disk
			time.sleep(3*self.data_logger.loop_interval)
			self.data_reader.RebuildCache()	
		elif 'time' in reading[origin_hourly] and utc_log_timestamp > reading[origin_hourly]['time']:
			self.logger.debug("New hourly value - log {0},{1}".format(utc_log_timestamp,precip_1hr))
			self.data_logger.LogData(origin_hourly,precip_1hr,timestamps=utc_log_timestamp)
		else:
			self.logger.debug("Same value at {0},{1} {2}".format(utc_log_timestamp,precip_1hr,reading))
			

# happy-case test
def logSomeData():
	
	dl=DataWriter(settings={'data_root':'data','data_url':url})
	dr=DataReader(settings={'data_root':'data'})
	dr.RebuildCache()
	tc=LogWebStuff(settings={'blocking':False,'data_logger':dl,'data_reader':dr})

	ctrl=autopool.logic.controller.Controller()
	ctrl.Run()
	ctrl.RunRecipe([dl,dr,tc])
	while ctrl.Status()==True:
		time.sleep(1)

logSomeData() # should run forever
