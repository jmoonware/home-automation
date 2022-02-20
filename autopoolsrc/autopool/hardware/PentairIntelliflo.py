# PentairIntelliflo.py
#
# 	Copyright (C) 2020  John Moon, jmpixelarium@gmail.com
#
#    This file is part of Autopool, Raspberry Pi control of a Pentair 
#    Intelliflo pool filter pump.
#
#    Autopool is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    Autopool is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with Autopool.  If not, see <https://www.gnu.org/licenses/>.
#
# Protocol, Packet Structure and Values obtained from: 
#  nodejs-poolController.  An application to control pool equipment.
#  Copyright (C) 2016, 2017.  Russell Goldin, tagyoureit.  russ.goldin@gmail.com
# See also https://github.com/tagyoureit/nodejs-poolController/wiki/Pumps
# 
# Note that Autopool is a simple master/slave system - the RPi controller expects the device (pump) to speak only when spoken to
# Generally each accepted controller packet is followed by a response packet which is either: 
# (1) an echo of the sent command (with SRC/DST reversed of course) (an ACK packet)
# (2) the requested information (e.g. status packet)
#
# If the device rejects the packet then a NACK packet is sent 
#
# Packet Structure (hex bytes)
# 	FF	00	FF	A5	00	DST	SRC	ACTION LENGTH	[PAYLOAD]	CSH	CSL
#	|_______|	|___|	|_______________________________|	|____|
#	   PRE	 	HEAD	              MSG                    CSUM
#
# where:
#
# PRE = Preamble (3 bytes, always FF 00 FF)
# HEAD = Header (2 bytes, always A5 00)	
# SRC = Source device (0x1x if sent from the "controller", here the RPi)
# DST = Destination device (0x6x if sent to the pump from the RPi, usually 0x60)
# ACTION = one of "WRITE"=1,"REMOTE"=4,"MODE"=5,"RUN"=6,"STATUS"=7
# LENGTH = number of PAYLOAD bytes (0-FF)
# [PAYLOAD] = series of bytes that contains the payload (which can contain futher commands and values for those commands)
# CSH = High byte of checksum
# CSL = Low byte of checksum
#
# Checksum is sum of all bytes starting with the A5 (inclusive) to the last byte (inclusive) of the payload
#
########################
# ACTION=WRITE=1 Packets
########################
# Command Packet:
# 	[PRE] [HEAD] DST SRC 01 04 CMD MODE VHIGH VLOW CSH CSL
#	 CMD = 3: Run Program
#		MODE = 0x21: V = 8*PROGRAM TO RUN (1,2,3,4); V=0 pump off
#		MODE = 0x27: V = RPM, program 1
#		MODE = 0x28: V = RPM, program 2
#		MODE = 0x29: V = RPM, program 3
#		MODE = 0x2A: V = RPM, program 4
#	CMD = 4: 
#		MODE = 0xC4: V=Set to RPM speed
#		MODE = 0xE4: V=Set to GPM speed
#	
# Response packet:
# 	[PRE] [HEAD] DST SRC 01 02 VHIGH VLOW CSH CSL

####################
# ACTION=REMOTE=4 
####################
# Command Packet:
# 	[PRE] [HEAD] DST SRC 04 01 SET CSH CSL
# 		SET = 0x00 (local, panel on pump on), 0xFF (remote, panel on pump off)
# Response Packet:
# 	[PRE] [HEAD] DST SRC 04 01 SET CSH CSL

####################
# ACTION=MODE=5 
####################
# Command Packet:
# 	[PRE] [HEAD] DST SRC 05 01 SET CSH CSL
# 		SET = 0 Set pump to Filter 
#			= 1 Set pump to Manual
#			= 2 Set pump to speed 1
#			= 3 Set pump to speed 2
#			= 4 Set pump to speed 3
#			= 5 Set pump to speed 4
# Response Packet:
# 	[PRE] [HEAD] DST SRC 05 01 SET CSH CSL

####################
# ACTION=RUN=6 
####################
# Command Packet:
# 	[PRE] [HEAD] DST SRC 06 01 SET CSH CSL
# 		SET = 0x04 (pump off), 0x0A (pump on)
# Response Packet:
# 	[PRE] [HEAD] DST SRC 06 01 SET CSH CSL

####################
# ACTION=STATUS=7 
####################
# Command Packet:
# 	[PRE] [HEAD] DST SRC 07 00 CSH CSL
# 		
# Response Packet:
# 	[PRE] [HEAD] DST SRC 07 0F [STATUS] CSH CSL
# where the (15) status bytes are:
#	0 = COMMAND (4=0ff, A=On)
#	1 = MODE
#	2 = Drivestate
#	3 = Watts High
#	4 = Watts Low
#	5 = RPM High
#	6 = RPM Low
#	7 = Flow
#	8 = PPC
# 	9 = TIMER?
#	10 = TIMER?
# 	11 = Status High
#	12 = Status Low
#	13 = Hours
#	14 = Mins
# 
# Note: Making the following structures classes allows e.g. Visual Studio Intellisense to work reasonably well
#

import queue

class PacketValues:
	def __init__(self):
		self.preamble=bytearray([0xFF,0x00,0xFF])
		self.header=bytearray([0xA5,0x00])
		self.PacketIndex=PacketIndex()
		self.Actions=PumpActions()
		self.WriteActions=PumpWriteAction()
		self.RemoteActions=PumpRemoteAction()
		self.RunActions=PumpRunAction()
		self.StatusIndex=PumpStatusIndex()
		self.ModeActions=PumpModeAction()
		
# all packets have these field indices		
class PacketIndex:
	""" Universal packet byte indices (relative to first HEADER byte) for every packet """
	def __init__(self):
		self.DST=2
		self.SRC=3
		self.ACTION=4
		self.LENGTH=5
		

class PumpActions:
	""" Value byte that can be in the ACTION field of the packet """
	def __init__(self):
		self.WRITE=1
		self.REMOTE=4
		self.MODE=5 
		self.RUN=6 
		self.STATUS=7 

class PumpWriteAction:
	""" Commands that can be contained in the payload of an ACTION=WRITE packet """
	def __init__(self):
		self.CMD_RUNPROGRAM=3
		self.CMD_RUNPROGRAM_MODE_PROGRAM=0x21
		self.CMD_RUNPROGRAM_MODE_P1RPM=0x27
		self.CMD_RUNPROGRAM_MODE_P2RPM=0x28
		self.CMD_RUNPROGRAM_MODE_P3RPM=0x29
		self.CMD_RUNPROGRAM_MODE_P4RPM=0x2A
		self.CMD_SET_SPEED=4
		self.CMD_SET_SPEED_MODE_RPM=0xC4
		self.CMD_SET_SPEED_MODE_GPM=0xe4

class PumpRemoteAction:
	""" Commands (and values) that can be contained in the payload of an ACTION=REMOTE packet """
	def __init__(self):
		self.LOCAL=0
		self.REMOTE=0xFF
		
class PumpModeAction:
	""" Commands (and values) that can be contained in the payload of an ACTION=MODE packet """
	def __init__(self):
		self.FILTER=0
		self.MANUAL=1
		self.SETSPEED1=2
		self.SETSPEED2=3
		self.SETSPEED3=4	
		self.SETSPEED4=5

class PumpRunAction:
	""" Commands (and values) that can be contained in the payload of an ACTION=RUN packet """
	def __init__(self):
		self.ON=0x0A
		self.OFF=0x04

class PumpStatusIndex: 
	""" Indices (relative to first HEADER byte) of pump status packet """
	def __init__(self):
		self.PAYLOAD_LENGTH=15
		self.CMD=6
		self.MODE=7 
		self.DRIVESTATE=8
		self.WATTSH=9
		self.WATTSL=10
		self.RPMH=11
		self.RPML=12
		self.GPM=13
		self.PPC=14
		self.ERR=15
		self.TIMER=18
		self.HOUR=19
		self.MIN=20
		
class PumpPacket:
	""" Constructs packets to send to pump and evaluates response """
	def __init__(self):
		self.pv=PacketValues()
		self.last_response=bytearray(0)
		self.expected_response=bytearray(0)
		# counters for packet statistics
		self.packets_sent=0
		self.packets_received=0
		self.packets_dropped=0
		self.packets_timeout=0
		self.packets_checksum=0
		self.dropped_packets=[] # keep a given number of dropped packets
		self.max_dropped_to_log=10 
		self.byte_timeout=3 # wait for a few seconds when parsing a packet queue before giving up
		self.last_response_state=1 # 0 if the last packet received is valid, non-zero otherwise

	def WriteActionPacket(self,dst,src,cmd,mode,value):
		""" 
		Send write command to pump - arguments: dst, src, cmd, mode, value 
		cmd and mode values defined in PumpWriteAction class
		If mode=CMD_RUNPROGRAM_MODE_PROGRAM provide the program number (1-4) as value
		If mode=CMD_RUNPROGRAM_MODE_PxRPM provide the RPM as value (x=1-4)
		"""
		if mode==self.pv.WriteActions.CMD_RUNPROGRAM_MODE_PROGRAM:
			v=(8*value).to_bytes(2,'big')
		else:
			v=value.to_bytes(2,'big')
		return(self.construct_packet(bytearray([dst,src,self.pv.Actions.WRITE,4,cmd,mode,v[0],v[1]])))
	def RemoteActionPacket(self,dst,src,set_to_remote=False):
		""" Set pump to local or remote - arguments: dst, src, set_to_remote=False """
		if set_to_remote:
			return(self.construct_packet(bytearray([dst,src,self.pv.Actions.REMOTE,1,self.pv.RemoteActions.REMOTE])))
		else:
			return(self.construct_packet(bytearray([dst,src,self.pv.Actions.REMOTE,1,self.pv.RemoteActions.LOCAL])))
	def ModeActionPacket(self,dst,src,mode=0):
		""" Set mode of pump - arguments: dst, src, mode=0 (a value from PumpModeAction class) """
		return(self.construct_packet(bytearray([dst,src,self.pv.Actions.MODE,1,mode])))
	def RunActionPacket(self,dst,src,run=False):
		""" Set run state of pump - arguments: dst, src, run=False """
		if run:
			return(self.construct_packet(bytearray([dst,src,self.pv.Actions.RUN,1,self.pv.RunActions.ON])))
		else:
			return(self.construct_packet(bytearray([dst,src,self.pv.Actions.RUN,1,self.pv.RunActions.OFF])))
	def StatusActionPacket(self,dst,src):
		""" Request status from pump - arguments: dst, src (usually 0x60, 0x10) """
		return(self.construct_packet(bytearray([dst,src,self.pv.Actions.STATUS,0])))
	def GetResponse(self,iq):
		""" gets the next valid packet from the byte queue, providing a timeout on each state transition """
		self.dropped_packets=[]
		#
		# I tested the performance of a Python queue object on my RPi3, and I got about 50 kBytes/second I/O, 
		# which is plenty fast enough for 9600 baud
		# Note that deque is ~20x faster at raw I/O, but does not have a timeout facility 
		# A timeout function for deque using datetime and a polling loop is about 1.5x (~70 kB/s) faster than queue
		# Using SIGALRM timeout method with deque is ~3x faster (~170 kB/s) than queue 
		# Using a polling sleep loop with a max number of iterations and deque is slightly faster than SIGALRM (~185 kB/s)
		# 
		# All methods 2-3x faster on an RPi4 BTW
		#
		# So queue is a good module to use in this case - adequate performance and less complicated
		#
		try:
			finished=False
			while not finished:
				# initialize response and state
				self.last_response=bytearray(0)
				self.last_response_state=1

				# scan for start of header byte
				while iq.get(timeout=self.byte_timeout)!=self.pv.expected_response[0]:
					continue	
				self.last_response_state+=1
				
				# header 1
				if self.check_byte(iq,1):
					continue

				# dst
				if self.check_byte(iq,self.pv.PacketIndex.DST):
					continue

				# src
				if self.check_byte(iq,self.pv.PacketIndex.SRC):
					continue
				
				# action
				if self.check_byte(iq,self.pv.PacketIndex.ACTION):
					continue
				
				# length
				if self.check_byte(iq,self.pv.PacketIndex.LENGTH):
					continue
				
				# now append payload length bytes and do checksum
				for i in range(self.last_response[self.pv.PacketIndex.LENGTH]):
					self.last_response.append(iq.get(timeout=self.byte_timeout))

				self.last_response_state+=1				
				# get the checksum bytes
				csh=iq.get(timeout=self.byte_timeout)
				csl=iq.get(timeout=self.byte_timeout)
				# checksum of incoming packet so far
				csv=sum(self.last_response)
				if(csh*256+csl != csv):
					self.packets_checksum+=1
					# don't take further action, although we should
				self.last_response_state+=1
				self.last_response.append(csh)
				self.last_response.append(csl)
				
				# we are done receiving a valid packet
				self.last_response_state=0
				finished=True
				self.packets_received+=1
		except queue.Empty: # timed out waiting for a byte
			self.packets_timeout+=1
	####
	# Helper functions
	####
	def check_byte(self,iq,idx):
		""" Check if next byte in input queue is correct and append for the packet we are processing """
		nb=iq.get(timeout=self.byte_timeout)
		if nb!=self.expected_response[idx]:
			# not correct - keep trying
			self.packets_dropped+=1
			if len(self.dropped_packets) < self.max_dropped_to_log:
				self.dropped_packets.append(bytearray(self.last_response))
			return True
		# if we got here then keep going
		self.last_response.append(nb)
		self.last_response_state+=1
		return False
		
	def construct_packet(self,msg):
		""" Add preamble, header, and checksum """
		self.set_expected_response(self.pv.header+msg)
		self.packets_sent+=1
		return(self.pv.preamble+self.pv.header+msg+self.checksum_bytes(self.pv.header+msg))
	def checksum_bytes(self,msg_with_header):
		""" Compute checksum and return high and low bytes """
		checksum=sum(msg_with_header)
		return(checksum.to_bytes(2,'big'))
	def set_expected_response(self,msg_with_header):
		""" 
		Function to set the expected response to each packet sent to pump 
		Used in loopback and integrity checks
		"""
		# swap source and destination, action is echoed
		self.expected_response=self.pv.header+bytearray([msg_with_header[self.pv.PacketIndex.SRC],msg_with_header[self.pv.PacketIndex.DST],msg_with_header[self.pv.PacketIndex.ACTION]])
		if msg_with_header[self.pv.PacketIndex.ACTION]==self.pv.Actions.WRITE:
			# return is value H/L or command/mode?
			self.expected_response.extend(bytearray([2,msg_with_header[self.pv.PacketIndex.LENGTH+3],msg_with_header[self.pv.PacketIndex.LENGTH+4]]))
		elif msg_with_header[self.pv.PacketIndex.ACTION]==self.pv.Actions.REMOTE:
			self.expected_response.extend(bytearray([1,msg_with_header[self.pv.PacketIndex.LENGTH+1]]))
		elif msg_with_header[self.pv.PacketIndex.ACTION]==self.pv.Actions.MODE:
			self.expected_response.extend(bytearray([1,msg_with_header[self.pv.PacketIndex.LENGTH+1]]))
		elif msg_with_header[self.pv.PacketIndex.ACTION]==self.pv.Actions.RUN:
			self.expected_response.extend(bytearray([1,msg_with_header[self.pv.PacketIndex.LENGTH+1]]))
		elif msg_with_header[self.pv.PacketIndex.ACTION]==self.pv.Actions.STATUS:
			# payload of all zeros for now
			self.expected_response.extend(bytearray([self.pv.StatusIndex.PAYLOAD_LENGTH])+bytearray(self.pv.StatusIndex.PAYLOAD_LENGTH)) 
		else: # unknown action
			self.expected_response=bytearray([ord('?'),msg_with_header[self.pv.PacketIndex.ACTION]])
		# add checksum to constructed response
		self.expected_response.extend(self.checksum_bytes(self.expected_response))
		return
