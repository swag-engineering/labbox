from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import sys

class Plot2D(pg.GraphicsLayoutWidget):
	def __init__(self, parent):		
		super().__init__(parent)
		self.traces = list()

		pg.setConfigOptions(antialias=True)
		pg.setConfigOption('foreground', 'k')

		self.plot = self.addPlot()
		self.plot.setMouseEnabled(x=False, y=False)
		self.plot.hideButtons()
		self.plot.showGrid(x=True, y=True)
