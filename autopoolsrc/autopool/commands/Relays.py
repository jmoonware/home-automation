
from autopool.logic.command import *
from autopool.devices import DIO

class RelayCommand(Command):
	def Init():
		self.edge_pump_relay=DIO.Get(pin=DIO.EDGE_PUMP_RELAY)
	def Execute():
