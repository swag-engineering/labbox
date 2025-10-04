from .defines import *
from .Config import Config
from .ui.Ui_LabBox import Ui_LabBox
from .Settings import Settings
from .GIFHandler import GIFHandler

import os
import sys
import serial
import numpy as np
from collections import deque
from itertools import islice

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QMainWindow
from PyQt5.QtCore import QRegExp, QTimer, Qt
from PyQt5.QtGui import QMovie, QRegExpValidator, QColor, QIcon, QPixmap



class LabBox(QMainWindow, Ui_LabBox):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.lineColors = Settings.byObject(self).lineColors
		self.pointsNumber = Settings.byObject(self).defaultPointsNumber
		self.reinit()
		self.setup()

	def reinit(self):
		self.microConnected = False
		self.port = None
		self.plotTimer = QTimer()
		self.sliderTimer = QTimer()		
		self.lastSliderValue = 0
		self.cfgData = CfgData()
		self.pointsStack = np.arange(0, self.pointsNumber, 1)
		self.plotStack = []
		self.csvPath = None
		self.csvFile = None
		self.timerValue = 0

	###GUI setups###
	def setup(self):
		self.setupUi(self)
		self.setFixedSize(self.size())
		self.statusBar().setSizeGripEnabled(False)
		self.usbRadioButton.setEnabled(False)
		self.usbRadioButton.toggled.connect(lambda: self.hideBaudrateField(True))
		self.serialRadioButton.toggled.connect(lambda: self.hideBaudrateField(False))

		self.devicePathLineEdit.setText(Settings.byObject(self).lastDevicePath or "")
		self.devicePathLineEdit.returnPressed.connect(self.onConnectButtonClick)
		self.deviceFolderButton.clicked.connect(self.onOpenDevicePathDialog)
		self.deviceFolderButton.setIcon(QIcon(QPixmap(
			os.path.join(Settings.icons_folder,"folder.png"))))

		self.csvPathLineEdit.setToolTip(Settings.byObject(self).csvPathLineEditTip)
		self.csvPathLineEdit.returnPressed.connect(self.onConnectButtonClick)
		self.csvFolderButton.clicked.connect(self.onOpenCSVPathDialog)
		self.csvFolderButton.setIcon(QIcon(QPixmap(
			os.path.join(Settings.icons_folder, "folder.png"))))

		self.baudrateComboBox.addItems(
			[str(baudRate) for baudRate in Settings.byObject(self).supportedBaudRates]
		)
		self.baudrateComboBox.setCurrentIndex(
			self.baudrateComboBox.findText(
				Settings.byObject(self).lastBaudrate, Qt.MatchFixedString
			)
		)

		self.cfgButton.setToolTip(Settings.byObject(self).cfgButtonTip)
		self.cfgButton.clicked.connect(self.onOpenCfgDialog)
		self.cfgButton.setIcon(QIcon(QPixmap(
			os.path.join(Settings.icons_folder, "gear.png"))))

		self.connectButton.clicked.connect(self.onConnectButtonClick)

		self.enableLeftPanel(False)

		self.mode1RadioButton.toggled.connect(
			lambda state: self.onModeChange(state, Playground.MODE_1)
		)
		self.mode2RadioButton.toggled.connect(
			lambda state: self.onModeChange(state, Playground.MODE_2)
		)
		self.mode3RadioButton.toggled.connect(
			lambda state: self.onModeChange(state, Playground.MODE_3)
		)

		self.button1.clicked.connect(
			lambda: self.write(Cmd.PLAYGROUND, Playground.BTN_1)
		)
		self.button2.clicked.connect(
			lambda: self.write(Cmd.PLAYGROUND, Playground.BTN_2)
		)

		self.valueLineEdit.setValidator(
			QRegExpValidator(QRegExp(Settings.byObject(self).valueLineEditRegex))
		)
		self.valueLineEdit.editingFinished.connect(self.sendLineEditValue)

		self.PointsNumberLineEdit.setText(
			str(Settings.byObject(self).defaultPointsNumber)
		)
		# TODO in the future will change it from points to freq, but idk for now how to implement it
		self.PointsNumberLineEdit.setValidator(
			QRegExpValidator(
				QRegExp(Settings.byObject(self).pointsNumberLineEditRegex),
			)
		)
		self.PointsNumberLineEdit.returnPressed.connect(self.onChangePointsNumber)

		# init plot
		self.plotView.setBackground(QColor(0xEF, 0xEF, 0xEF))
		self.plotView.plot.setContentsMargins(10, 0, 10, 0)
		self.plotView.plot.setXRange(0, self.pointsNumber, padding=0)

		# enable blinking animation
		# self.beemoLabel.startMain(QMovie("img/staying.gif", parent=self.beemoLabel))
		# self.beemoLabel.setPeriodically(QMovie("img/blinking.gif", parent=self.beemoLabel), 2000)

	def sendLineEditValue(self):
		if self.microConnected:
			self.write(Cmd.PLAYGROUND, Playground.LINE_EDIT, 
				int(self.valueLineEdit.text()))

	def sendSliderValue(self):
		sliderValue = self.slider.value()
		if self.lastSliderValue != sliderValue:
			self.write(Cmd.PLAYGROUND, Playground.SLIDER, int(sliderValue))
			self.lastSliderValue = sliderValue

	def onModeChange(self, state: bool, mode: Playground):
		try:
			if state and self.microConnected:
				self.write(Cmd.PLAYGROUND, mode)
		except RuntimeError as e:
			QMessageBox.warning(
				self, "Error", str(e), QMessageBox.Ok
			)

	def initPlayground(self):
		self.sendSliderValue()
		self.sendLineEditValue()
		self.lastSliderValue = 0
		self.sliderTimer.timeout.connect(self.sendSliderValue)
		self.sliderTimer.start(self.cfgData.updateTime)

	def deinitPlayground(self):
		self.sliderTimer.stop()
		self.mode1RadioButton.setAutoExclusive(False)
		self.mode2RadioButton.setAutoExclusive(False)
		self.mode3RadioButton.setAutoExclusive(False)
		self.mode1RadioButton.setChecked(False)
		self.mode2RadioButton.setChecked(False)
		self.mode3RadioButton.setChecked(False)
		self.mode1RadioButton.setAutoExclusive(True)
		self.mode2RadioButton.setAutoExclusive(True)
		self.mode3RadioButton.setAutoExclusive(True)
		self.valueLineEdit.setText("0")
		self.slider.setValue(0)

	def onOpenDevicePathDialog(self):
		devPathLineDialog = QFileDialog()
		pathExport, _ = devPathLineDialog.getOpenFileName(
			self, "Open file", "/dev/", "Device (*)"
		)
		self.devicePathLineEdit.setText(pathExport)

	def onOpenCSVPathDialog(self):
		csvPathLineDialog = QFileDialog()
		pathSave, _ = csvPathLineDialog.getSaveFileName(
			self, "Save File", "/home/", "CSV (*.csv);;All files (*.*)"
		)
		self.csvPathLineEdit.setText(pathSave)

	def onOpenCfgDialog(self):
		cfgDialog = Config(self)
		# cfgDialog.layout().setSizeConstraint(QLayout.SetFixedSize)
		cfgDialog.open()

	def closeEvent(self, event):
		reply = QMessageBox.question(
			self,
			"Message",
			"Do you want to save settings?",
			QMessageBox.Yes,
			QMessageBox.No,
		)

		if reply == QMessageBox.Yes:
			Settings.byObject(self).lastDevicePath = \
				self.devicePathLineEdit.text()
			Settings.byObject(self).lastBaudrate = \
				self.baudrateComboBox.currentText()
			Settings.saveSettings()
		if self.microConnected:
			self.disconnectMicro()
		event.accept()

	def enableLeftPanel(self, state):
		self.signalFunctionBox.setEnabled(state)  # now we put it in single groupbox

	def onConnectButtonClick(self):
		if not self.microConnected:
			try:
				self.reinit()

				# forbidding user to click it while connecting
				self.connectButton.setEnabled(False)
				self.connectMicro()
				self.connectButton.setEnabled(True)
				self.microConnected = True
				self.connectButton.setText("Disconnect")
				self.connectionGroupBox.setEnabled(False)
				self.devicePathLineEdit.setEnabled(False)
				self.baudrateComboBox.setEnabled(False)
				self.csvPathLineEdit.setEnabled(False)
				self.initPlot()
				self.initPlayground()
				# enable jumping animation
				# self.beemoLabel.playOnce(QMovie("img/jumping.gif"), priority=True)
			except (ValueError, FileNotFoundError, PermissionError, RuntimeError) as e:
				QMessageBox.warning(
					self, "Error", str(e), QMessageBox.Ok
				)
				self.connectButton.setEnabled(True)
				return
			except Exception as e:
				QMessageBox.warning(
					self,
					"Error",
					"Unexpected exception occured:\n" + str(e),
					QMessageBox.Ok,
				)
				self.onConnectButtonClick()
				return
		else:
			try:
				self.deinitPlot()
				self.deinitPlayground()
			except Exception as e:
				QMessageBox.warning(
					self,
					"Error",
					"Unexpected exception occured:\n" + str(e),
					QMessageBox.Ok,
				)
				raise
			self.disconnectMicro()
			if self.csvPath:
				self.csvFile.close()
			self.connectButton.setEnabled(True)
			self.connectButton.setText("Connect")
			self.microConnected = False
			self.connectionGroupBox.setEnabled(True)
			self.devicePathLineEdit.setEnabled(True)
			self.baudrateComboBox.setEnabled(True)
			self.csvPathLineEdit.setEnabled(True)

	def onChangePointsNumber(self):
		pointsNumber = self.PointsNumberLineEdit.text()
		if not pointsNumber:
			QMessageBox.warning(
				self, "Error", "Field can't be empty!", QMessageBox.Ok
			)
			return
		self.pointsNumber = int(pointsNumber)
		self.pointsStack = np.arange(0, self.pointsNumber, 1)
		for i in range(len(self.cfgData.namesList)):
			if self.pointsNumber > len(self.plotStack[i]):
				self.plotStack.append(deque(
					list(islice(self.plotStack[i], 0, len(self.plotStack[i]))),
					maxlen=self.pointsNumber,
				))
			else:
				self.plotStack[i] = deque(
					list(
						islice(self.plotStack[i],
							len(self.plotStack[i]) - self.pointsNumber,
							len(self.plotStack[i]),
						)
					),
					maxlen=self.pointsNumber,
				)

		self.plotView.plot.setXRange(0, self.pointsNumber, padding=0, update=False)

	def connectMicro(self):
		self.openPort()
		self.configureComm()

	def openPort(self):
		if self.serialRadioButton.isChecked():
			devicePath = self.devicePathLineEdit.text()
			if not devicePath:
				raise ValueError("Field 'Device path' can't be empty!")
			elif not os.access(devicePath, os.F_OK):
				raise FileNotFoundError("No such device file!")
			elif not os.access(devicePath, os.R_OK | os.W_OK):
				raise PermissionError(
					"Device file:\nRead and/or write permission denied!"
				)
			# init serial port
			self.port = serial.Serial(
				port=devicePath,
				baudrate=int(self.baudrateComboBox.currentText()),
				parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS,
				timeout=0.1,  # 100ms
			)
			self.csvPath = self.csvPathLineEdit.text()
			if self.csvPath:
				if not os.path.isdir(os.path.dirname(self.csvPath)):
					raise FileNotFoundError(
						"Invalide path:\n" + self.csvPath + " does not exist!"
					)
				elif not os.access(os.path.dirname(self.csvPath), os.W_OK):
					raise PermissionError(
						"CSV file:\nRead and/or write permission denied!"
					)
				else:
					pass
		elif self.usbRadioButton.isChecked():
			pass


	def write(self, cmd, pg=None, data=None):
		if self.serialRadioButton.isChecked():
			try:
				if pg:
					cmd |= pg << 8 * 2
				if data:
					cmd |= data
				array = cmd.to_bytes(Cmd.SIZE, byteorder='little')
				return self.port.write(array)
			except serial.SerialTimeoutException:
				raise RuntimeError("Timeout elapsed!")
			except serial.SerialException as e:
				raise RuntimeError("Unexpected SerialException occured!\n" + str(e))
		elif self.usbRadioButton.isChecked():
			pass

	def read(self, size=1, raiseTimeout=True) -> bytes:
		if self.serialRadioButton.isChecked():
			try:
				data = self.port.read(size=size)
				if data is not None:
					return data
				elif raiseTimeout:
					raise RuntimeError("Timeout elapsed!")
			except serial.SerialException as e:
				raise RuntimeError("Unexpected SerialException occured!\n" + str(e))
		elif self.usbRadioButton.isChecked():
			pass

	def readInt(
		self, size=1, signed=False, raiseTimeout=True
	) -> int:  # Could be changed when usb added
		data = self.read(size=size, raiseTimeout=raiseTimeout)
		return int.from_bytes(data, signed=signed, byteorder="little")

	def configureComm(self):
		self.write(Cmd.PC_HELLO)
		if self.readInt(size=4) != Cmd.CFG_START:
			raise ValueError(f"No config start byte from micro was detected.")

		self.cfgData.graphNumbers = self.readInt(size=1)
		self.cfgData.maxVoltage = self.readInt(size=2, signed=True) * 1.1
		self.cfgData.minVoltage = self.readInt(size=2, signed=True) * 1.1
		self.cfgData.updateTime = self.readInt(size=1)
		for i in range(self.cfgData.graphNumbers):
			length = self.readInt()
			data = self.read(size=length)
			name = data.decode("utf-8")
			self.cfgData.namesList.append(name)

		if self.csvPath:
			self.csvFile = open(self.csvPath, "w")
			self.csvFile.writelines([", ".join(
				sName for sName in self.cfgData.namesList), ", ", "time", "\n"])
			

	def disconnectMicro(self):
		if self.serialRadioButton.isChecked():
			if self.port.isOpen():
				try:
					self.write(Cmd.PC_BYE)
				except Exception as e:
					pass
				self.port.close()
		if self.usbRadioButton.isChecked():
			pass

	def initPlot(self):
		self.plotView.plot.addLegend()
		self.plotView.plot.setYRange(
			self.cfgData.minVoltage,
			self.cfgData.maxVoltage,
			padding=0,
			update=False,
		)

		for i in range(self.cfgData.graphNumbers):
			self.plotView.traces.append(self.plotView.plot.plot(
				pen=self.lineColors[i], name=self.cfgData.namesList[i]
			))
			self.plotStack.append(deque(maxlen=self.pointsNumber))
		self.enableLeftPanel(True)
		self.plotTimer.timeout.connect(self.updatePlot)
		self.plotTimer.start(self.cfgData.updateTime)

	def updatePlot(self):
		try:
			if self.readInt(size=Cmd.SIZE, raiseTimeout=False) == Cmd.DATA_START:
				k = 1
				for i in range(self.cfgData.graphNumbers):
					data = self.readInt(
						size=2, signed=True, raiseTimeout=False
					)
					self.plotStack[i].append(data)
					self.plotView.traces[i].setData(
						self.pointsStack[: len(self.plotStack[i])],
						self.plotStack[i],
					)
					if self.csvPath:
						self.csvFile.write(str(data))
						if k != self.cfgData.graphNumbers:
							self.csvFile.write(", ")
							k += 1
						else:
							self.csvFile.writelines([", ", "{:.2f}".format(self.timerValue), "\n"])

				self.timerValue += self.plotTimer.interval() * 0.01
		except RuntimeError as e:
			self.onConnectButtonClick()
			QMessageBox.warning(
				self, "Error", str(e), QMessageBox.Ok
			)

	def deinitPlot(self):
		self.plotTimer.stop()
		self.plotView.plot.legend.clear()
		for i in range(self.cfgData.graphNumbers):
			self.plotStack[i].clear()
			self.plotView.traces[i].setData(
				self.pointsStack[: len(self.plotStack[i])],
				self.plotStack[i],
			)
		self.enableLeftPanel(False)

	def hideBaudrateField(self, state):
		if not state:
			self.deviceBaudrateLabel.show()
			self.baudrateComboBox.show()
		else:
			self.deviceBaudrateLabel.hide()
			self.baudrateComboBox.hide()
