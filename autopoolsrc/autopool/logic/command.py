import logging
import threading
from autopool.logic.worker import *

class Command(Worker):
	def __init__(self,settings=None):
		# set to a string value to label this commands program counter
		self.branch_tag=None
		# set to a valid branch_tag to go to that command's program counter
		self.branch_to=None 
		super().__init__(settings=settings)

#
# Example command
#
class ExampleCommand(Command):
	def Init(self): # extend class variables here
		self.parm1=1
	def Execute(self): # add logic for command
		self.logger.error("{0} Parm1={1}".format(self,self.parm1))
