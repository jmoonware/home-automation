import glob
import sys
import datetime
import logging

path_1w='/sys/bus/w1/devices/28*/w1_slave'

class DS18B20():
	def __init__(self,device_path=None,device_name=None):
		self.device_paths=[]
		self.device_names=[]
		if device_path:
			self.device_paths.append(device_path)
			self.device_names.append(device_name)
		self.logger=logging.getLogger(__name__)
		if len(self.device_paths)==0:
			self.devs=glob.glob(path_1w)
			self.logger.debug("Found 1-wire {0}".format(self.devs))
			if len(self.devs) > 0:
				for p in self.devs:
					self.device_paths.append(p)
					s=p.split('/')
					if len(s) > 1:
						self.device_names.append(s[-2])
					else:
						self.device_names.append(s)
					self.logger.info("Using {0}".format(p))
			else:
				raise RuntimeError("No 1-wire devices found in {0}".format(path_1w))

	def LogTemperature(self):
		ret={}
		for p,n in zip(self.device_paths,self.device_names):
			lines=[]
			if p:
				with open(p,'r') as f:
					lines=f.readlines()
			else:
				self.logger.debug("No device found")
				return
			TC=-999
			for l in lines:
				if "t=" in l:
					TC=float(l.split('t=')[1])*1e-3
			fields=[]
			fields.append("{0} T=".format(n))
			fields.append("{0:.3f} C".format(TC))
			fields.append("{0:.3f} F".format(32+(9*TC/5)))
			self.logger.info('\t'.join(fields))
			ret[n]=TC
		return(ret)
