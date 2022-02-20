import logging
import threading
import time
from collections import deque
import sys,traceback
from autopool.logic.worker import *

class Controller(Worker):
	def Init(self,logFile="log.txt",settings=None):
#		super().__init__(settings=settings)
		self.timeout=10 # allow this time for orderly shutdown
		self.done=False
		# internal variables
		self._thread=None
		self.recipe=[] # list of commands
		self.recipe_lock=threading.Lock()
		self.running_commands=deque()
		self.loop_interval=1
		self.loop_count=-1
		self.blocking=False
		self.program_counter=0
		self.branch_tags={}
		self.quiet=True # suppress routine debug messages
		# keep count of exceptions
		self.max_exception_count=10 # die after this many command exceptions
		self.once=False # if true, end controller loop when idle
#	def Start(self):
#		if self._thread!=None:
#			self.Stop()
#		self._thread=threading.Thread(target=self._loop)
#		self.done=False
#		self._thread.daemon=True
#		self._thread.start()
#		self.logger.info("Controller started...")
#	def Stop(self):
#		self.done=True
#		if self.Status():
#			self._thread.join(self.timeout)
#			if self.Status(): 
#				self.logger.error("{0} timeout during Stop".format(self))		
#			self.logger.info("Controller stopped")
#		else:
#			self.logger.warning("Controller already stopped")
	def StopRunningCommands(self):
		stillRunning=[]
#		self.logger.debug("{0}:  Shutting down commands...".format(self))
		while len(self.running_commands) > 0:
			c=self.running_commands.popleft()
			self.logger.debug("{0} {1} Command Stop".format(self,c))
			c.Stop()
			if c.Status()!=False:
				stillRunning.append(c)
		if len(stillRunning) > 0:
			self.logger.warning("{0}: Unable to shut down commands {1}".format(self,stillRunning))
			self.running_commands.extend(stillRunning)
	def __str__(self):
		return(self.Prefix()+",THD={0},PC={1},RC={2})".format(self.Status(),self.program_counter,len(self.running_commands)))
	def CommandStatus(self):
		msg=["{0} CommandStatus".format(self)]
		for c in self.recipe:
			msg.append("{0}: {1}".format(c,c.Status()))
		self.logger.debug(','.join(msg))
		return(','.join(msg))
	def VerboseStatus(self):
		msg="{0} VerboseStatus {1}".format(self,self.running_commands)			
		self.logger.debug(msg)
		return(msg)
	def Enter(self):
		self.logger.info(format("{}: Controller started".format(self)))
		self.total_running_exceptions=0
	def Execute(self):
#	while not self.done and self.exception_count+total_running_exceptions < self.max_exception_count:
		try:
			next_command=None
			with self.recipe_lock:
				if self.program_counter < len(self.recipe):
					next_command=self.recipe[self.program_counter]	
					self.program_counter+=1
			if next_command:
				next_command.Run()
				# will probably miss non-blocking exceptions 
				if next_command.exception:
					self.logger.error("{0}:{1}: Exception {2}".format(self,next_command,next_command.exception)) 
					self.exception_count+=1
				# will collect all unblocked whether running or not
				# will also collect all running join-timeout commands
				if next_command.blocking==False or next_command.Status():
					self.running_commands.append(next_command)
				else: # check for branch
					if next_command.branch_to:
						if next_command.branch_to in self.branch_tags.keys():
							with self.recipe_lock:
								self.program_counter=self.branch_tags[next_command.branch_to]
						else:
							logger.error("{0} attempt branch to {1}: available branch tags = {2} - disabling".format(self,next_command.branch_to,self.branch_tags))
							next_command.branch_to=None # reset
			else:
				if not self.quiet:
					self.logger.debug("idle")
				time.sleep(self.loop_interval)
				if self.once: # once Controller is idle then end
					self.done=True
			# count how many exceptions we have in non-blocking
			self.total_running_exceptions=0
			for c in self.running_commands:
				self.total_running_exceptions+=c.exception_count
		except Exception as ex:
			self._exception_handler(ex,"In Controller:")
		self.exception_count+=self.total_running_exceptions
		if self.exception_count >= self.max_exception_count:
			self.logger.error("Max exception count reached - goodbye")
			self.done=True
	def Exit(self):
		self.StopRunningCommands()
		self.logger.info("{0}: Controller exit".format(self))
	def RunRecipe(self,recipe,once=False):
		try:
			self.StopRunningCommands()
			with self.recipe_lock:
				self.recipe=recipe
				self.branch_tags={}
				for pc,c in enumerate(recipe):
					if c.branch_tag:
						self.branch_tags[c.branch_tag]=pc
				self.program_counter=0
				self.once=once
				if self.once:
					self.Run()
		except AttributeError as ae:
			self._exception_handler(ae,"In RunRecipe")
	def RunCommand(self,command,once=False):
		self.RunRecipe([command],once)
