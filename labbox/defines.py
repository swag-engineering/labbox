class Cmd:
	SIZE = 4
	PC_HELLO = 0xAA << 8 * (SIZE -1)
	CFG_START = 0xBB << 8 * (SIZE -1)
	DATA_START = 0xCC << 8 * (SIZE -1)
	PLAYGROUND = 0xDD << 8 * (SIZE -1)
	PC_BYE = 0xFF << 8 * (SIZE -1)


class Playground:
	MODE_1 = 0xD1
	MODE_2 = 0xD2
	MODE_3 = 0xD3
	BTN_1 = 0xB1
	BTN_2 = 0xB2
	LINE_EDIT = 0xED
	SLIDER = 0xDE
	SIZE = 1

class CfgData:
	def __init__(self):
		self.namesList = []
		self.graphNumbers = 0
		self.maxVoltage = 0
		self.minVoltage = 0
		self.updateTime = 0
