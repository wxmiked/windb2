import math

class FlowData(object):

	"""Datatime of the observation time."""
	time = None
	
	"""Height above ground level [m]"""
	height = None
	
	"""Speed in units"""
	speed = None
	
	"""Units of speed."""
	units = None
	
	"""Direction [degrees]"""
	direction = None
	

	"""Creates a new FlowData object"""
	def __init__(self, time, height, speed, direction, units = "ms^-1"):
		self.time = time
		self.height = float(height)
		self.speed = float(speed)
		self.units = units
		self.direction = float(direction)
		
	"""Returns the speed in the U direction."""
	def getUSpeed(self):
		return math.sin(math.radians(self.direction)) * self.speed
	
	"""Returns the speed in the V direction."""
	def getVSpeed(self):
		return math.cos(math.radians(self.direction)) * self.speed
	
	"""Prints the flow data in a pretty fashion."""
	def __str__(self):
		return 'time=' + str(self.time) + ' height=' + str(self.height) + ' speed=' + str(self.speed) + ' ' + \
			str(self.units) + ' at ' +  str(self.direction) + ' deg '
