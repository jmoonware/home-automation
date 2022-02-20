
import sys, logging, traceback

class ExceptionHandler():
	def __init__(self,name):
		self.exception=None
		self.exception_count=0
		self.logger=logging.getLogger(name)
		self.name=name
	def Handle(self,ex,msg):
		self.logger.error("{0} {1} {2}".format(self.name,msg,ex))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		self.logger.debug(traceback.format_tb(exc_traceback))
		self.exception=ex
		self.exception_count+=1

