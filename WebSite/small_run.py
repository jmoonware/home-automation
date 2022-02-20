import logging
import autopool
import autopool.app
from autopool.logic.command import *
from autopool.commands.DataLogger import DataLogger
from autopool.devices.WindDevice import WindDevice
import time

autopool.app.start_logging(level=logging.DEBUG,filename='windlog.txt')
url='http://ec2-13-59-78-131.us-east-2.compute.amazonaws.com:8084/sensors'

# here are some origin,data pairs

class LogWindValues(Command):
	def Init(self):
		self.wd=WindDevice(settings={'simulated':False})
	def Execute(self):
		vmph=self.wd.ReadWindSpeed()
		angle=self.wd.ReadWindDirection()
		self.data_logger.LogData('wind_vmph',vmph)
		self.data_logger.LogData('wind_angle',angle)

# happy-case test
def logSomeData():
	dl=DataLogger(settings={'data_root':'data','data_url':url})
	tc=LogWindValues(settings={'blocking':False,'loop_count':-1,'loop_interval':2,'data_logger':dl})
	ctrl=autopool.logic.controller.Controller()
	ctrl.Run()
	ctrl.RunRecipe([dl,tc])
	while ctrl.Status()==True:
		time.sleep(1)

logSomeData() # should run forever
