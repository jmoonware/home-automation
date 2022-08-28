import threading, logging
from autopool.logic.exception_handler import *

# The Device class builds in simulation capability for each piece of hardware
# Each device class should override {Dev,Sim} Init, Action, Shutdown
# Actions have one (string, device dependent) argument called 'action'
# For instance, most devices will have a 'Status' action; some might have a
# 'Read' or 'Write' action
class Device():
	def __init__(self,settings=None):
		self.simulated=True # default to simulation - override in settings
		if settings:
			for k in settings:
				self.__dict__[k]=settings[k]
		self.settings=settings
		self.logger=logging.getLogger(__name__)
		self.eh=ExceptionHandler(__name__)
		# use this in calls to protect against multiple threads
		self.sync=threading.Lock()
		try:
			self.Init()
		except Exception as ex:
			self.eh.Handle(ex,"In Device Init():")
	def Init(self):
		if self.simulated:
			self.SimInit()
		else:
			self.DevInit()
	# override these for simulated or physical device Init
	def SimInit(self):
		self.logger.debug("{0} Device generic simulated init".format(self))
	def DevInit(self):
		self.logger.debug("{0} Device generic device init".format(self))
	def Action(self,action='Status'):
		if self.simulated:
			self.SimAction(action)
		else:
			self.DevAction(action)
	def SimAction(self,action):
		self.logger.debug("{0} Device generic simulated action".format(self))
	def DevAction(self,action):
		self.logger.debug("{0} Device generic device action".format(self))
	def Shutdown(self):
		if self.simulated:
			self.SimShutdown()
		else:
			self.DevShutdown()
	def SimShutdown(self):
		self.logger.debug("{0} Device generic simulated shutdown".format(self))
	def DevShutdown(self):
		self.logger.debug("{0} Device generic device shutdown".format(self))
