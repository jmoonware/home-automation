import serial
import logging
import threading
import queue
from autopool.logic.device import *
from autopool.logic.worker import *

class SerialDevice(Device):
	def DevInit(self):
		self.worker=SerialWorker(self.settings)
	def SimInit(self):
		self.worker=None
	def SimAction(self,action):
		if action=='Read':
			self.logger.info("Simulated Serial Read")
		elif action=='Status':
			self.logger.info("Simulated Serial Status")

class SerialWorker(Worker):
	""" 
	Instance of a serial device (constructor accepts settings dict)
	Read bytes get added to iq asynchronously
	Write is currently synchronous 
	"""
	def Status(self):
		self.logger.debug("{0}:{1}".format(self,self._serial))
		return(super().Status())
	def Enter(self):
		if self._serial==None:
			raise ValueError("Read: Device {0} has not been opened".format(self.port))
	def Execute(self):
		""" Loop running in independent thread to read serial port and enqueue """
		current_backlog=max(self._serial.inWaiting(),1)
		new_bytes=self._serial.read(current_backlog)
		if len(new_bytes)==0: # timeout, nothing in buffer
			self.logger.debug('Waiting on {0}'.format(self.port))
		else:
			for x in new_bytes:
				self.iq.put(x)
			self.logger.debug('Received:\t{0}'.format(' '.join(['{0:02x}'.format(x) for x in new_bytes])))
	def Write(self,data):
		""" Function to write bytearray buffer to serial port """
		try:
			if self._serial==None:
				raise ValueError("Write: Device {0} has not been opened".format(self.port))
			self._serial.write(data)
			self.logger.debug("Sent:\t{0}".format(' '.join(['{0:02x}'.format(x) for x in data])))
		except serial.SerialException as se:
			self.logger.error(se)
		except ValueError as ve:
			self.logger.error(ve)
	def Init(self):
		""" Call open first before attempting to read/write to serial port """
		# update defaults if not specified
		self._serial=None
		self.iq=queue.Queue()
		self.blocking=False
		self.loop_count=-1
		self.serial_timeout=0.2
		# last chance to populate settings
		if self.settings==None:
			self.settings={}
		if not 'port' in self.settings:
			self.port='/dev/ttyS0'
		if not 'loop_interval' in self.settings:
			self.loop_interval=0.05
		self._serial=serial.Serial(self.port,timeout=self.serial_timeout)
		self.logger.info("{0}".format(self._serial))
	def Shutdown(self):
		self.Stop()
		if self._serial:
			self._serial.close()
