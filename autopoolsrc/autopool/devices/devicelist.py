from autopool.devices.ADCDevice import *
from autopool.devices.DIODevice import *
from autopool.devices.PumpDevice import *
from autopool.devices.SerialDevice import *
from autopool.devices.ThermalDevice import *

# each entry is a single physical device
DeviceList={
	"theADCDevice":ADCDevice(settings={"simulated":True}),
	"theDIODevice":DIODevice(settings={"simulated":True}),
	"thePumpDevice":PumpDevice(settings={"simulated":True}),
	"theSerialDevice":SerialDevice(settings={"simulated":True}),
	"theThermalDevice":ThermalDevice(settings={"simulated":True})
}

