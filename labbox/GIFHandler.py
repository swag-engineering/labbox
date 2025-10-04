from PyQt5 import QtCore, QtWidgets
from collections import deque


class GIFHandler(QtWidgets.QLabel):
	"""docstring for GIFHandler"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.queue = deque()
		self.main = None
		self.current = None
		self.timer = QtCore.QTimer(self)

	def finishIfDone(self, current):
		if current.currentFrameNumber() == current.frameCount() - 1:
			current.stop()
			current.frameChanged.disconnect()
			self.onFinish()

	def startMain(self, main):
		self.main = main
		self.onFinish()

	def playOnce(self, movie, priority=False):
		if priority:
			self.queue.appendleft(movie)
		else:
			self.queue.append(movie)

	def onFinish(self):
		if bool(len(self.queue)):
			current = self.queue.popleft()
		else:
			current = self.main
		self.setMovie(current)
		current.frameChanged.connect(lambda: self.finishIfDone(current))
		current.start()

	def setPeriodically(self, movie, time):
		# time in ms
		self.timer.setInterval(time)
		self.timer.timeout.connect(lambda: self.playOnce(movie))
		self.timer.start()




