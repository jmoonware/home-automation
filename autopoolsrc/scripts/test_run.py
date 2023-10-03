import logging
import autopool
import autopool.app
from autopool.logic.command import *
from autopool.commands.DataLogger import DataWriter
from autopool.commands.DataLogger import DataReader
from autopool.commands.LogWeb import LogWebCommand
import time

autopool.app.start_logging(level=logging.DEBUG,filename='testlog.txt')
url='http://localhost:8050/sensors'

origin_hourly = 'precip_inphr'
origin_daily = 'precip_inpday'

# happy-case test
def logSomeData():
	
	dw=DataWriter(settings={'data_root':'data','data_url':url})
	dr=DataReader(settings={'data_root':'data'})
	dr.RebuildCache()
	tc=LogWebCommand(settings={'blocking':False,'data_logger':dw,'data_reader':dr})

	ctrl=autopool.logic.controller.Controller()
	ctrl.Run()
	ctrl.RunRecipe([dw,dr,tc])
	while ctrl.Status()==True:
		time.sleep(1)

logSomeData() # should run forever
