import RPi.GPIO as GPIO

# BCM values (i.e. chip pin, NOT header pin #) 
PinsOut={
'FILL_RELAY':22, # J8 Header pin 15 
'EDGE_RELAY':17 # J8 Header pin 11
}

class Relays():
	def __init__(self):
		GPIO.setmode(GPIO.BCM)
		for p in PinsOut:
			GPIO.setup(PinsOut[p], GPIO.OUT)
	# do I need these wrappers? Not doing anything
	def Set(self,pin=PinsOut['FILL_RELAY'],state=GPIO.LOW):
		GPIO.output(pin,state)
	def Get(self,pin=PinsOut['FILL_RELAY']):
		return(GPIO.input(pin))

