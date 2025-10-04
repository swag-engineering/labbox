from .defines import Cmd
from .Settings import Settings
from .ui.Ui_Config import Ui_Config

from PyQt5.QtCore import QSize, QRegExp
from PyQt5.QtGui import QRegExpValidator, QCloseEvent
from PyQt5.QtWidgets import QDialog, QLineEdit


class Config(QDialog, Ui_Config):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.generateButton.setEnabled(False)
        self.signalsNumberLabel.setToolTip(Settings.byObject(self).signalsNumberTip)
        self.signalNameLabel.setToolTip(Settings.byObject(self).signalNameTip)
        self.minVoltageLabel.setToolTip(Settings.byObject(self).minVoltageTip)
        self.maxVoltageLabel.setToolTip(Settings.byObject(self).maxVoltageTip)
        self.updateTimeLabel.setToolTip(Settings.byObject(self).updateTimeTip)
        self.generateButton.clicked.connect(self.generate)
        self.signalsNumberSpinBox.valueChanged.connect(self.manageNamesLines)
        self.signalNameLineEdit.setValidator(
            QRegExpValidator(
                QRegExp(Settings.byObject(self).textRegex)
            )
        )
        self.signalNameLineEdit.textEdited.connect(
            lambda: self.onLineEdit(self.signalNameLineEdit)
        )
        defaultDataLength = int(Settings.byObject(self).defaultDataLength, 16) / 2
        self.minVoltageSpinBox.setMinimum(defaultDataLength * -1)
        self.minVoltageSpinBox.setMaximum(0)
        self.minVoltageSpinBox.setSingleStep(100)
        self.minVoltageSpinBox.setProperty(
            "value", Settings.byObject(self).lastMinVoltage
        )

        # min by default 0
        self.maxVoltageSpinBox.setMaximum(defaultDataLength)
        self.maxVoltageSpinBox.setSingleStep(100)
        self.maxVoltageSpinBox.setProperty(
            "value", Settings.byObject(self).lastMaxVoltage
        )

        self.updateTimeSpinBox.setMinimum(10)
        self.updateTimeSpinBox.setMaximum(200)
        self.updateTimeSpinBox.setSingleStep(10)
        self.updateTimeSpinBox.setProperty(
            "value", Settings.byObject(self).lastUpdateTime
        )

        self.signals = [self.signalNameLineEdit]  # by default we start with 1 signal

        self.doneDict = {
            self.signals[0]: False  # we remove default value so it's False now
        }

        self.styleBackup = self.signalNameLineEdit.styleSheet()

    def manageNamesLines(self):
        """
		Checks if new name line need to be added are removed
		:return:
		"""
        count = self.signalsNumberSpinBox.value() - len(self.signals)
        if count > 0:
            self.addNewSignalNameLineEdit(count)
        else:
            self.removeSignalNameLineEdit(count)
        self.enableGenerateButton()

    def addNewSignalNameLineEdit(self, count: int):
        """
		Adds new signal name lines
		:return:
		"""
        while count > 0:
            newSignal = QLineEdit(self)
            newSignal.setMaximumSize(QSize(150, 30))
            newSignal.setMinimumSize(QSize(150, 30))
            self.formLayout.insertRow(len(self.signals) + 1, "", newSignal)
            newSignal.setValidator(
                QRegExpValidator(
                    QRegExp(Settings.byObject(self).textRegex)
                )
            )
            newSignal.textEdited.connect(lambda: self.onLineEdit(newSignal))
            if newSignal not in self.doneDict:
                self.doneDict[newSignal] = False
            self.signals.append(newSignal)
            count -= 1

    def removeSignalNameLineEdit(self, count: int):
        """
		Removes signal name lines
		:param count: 
		:return: 
		"""
        while count < 0:
            self.formLayout.removeWidget(self.signals[count])
            self.signals[count].deleteLater()
            del self.doneDict[self.signals[count]]
            del self.signals[count]
            self.formLayout.activate()
            self.resize(self.sizeHint())
            count += 1

    def onLineEdit(self, textLine: QLineEdit):
        """
		Checks validation for text edit lines
		:param textLine:
		:return:
		"""
        text = textLine.text()
        if not text:
            self.declineLineEdit(textLine)
        else:
            self.acceptLineEdit(textLine, text)
        self.enableGenerateButton()

    def acceptLineEdit(self, line: QLineEdit, text: str):
        """
        Accepts text in line edit
        :return:
        """
        line.setText(text)
        line.setStyleSheet(self.styleBackup)
        self.doneDict[line] = True

    def declineLineEdit(self, line: QLineEdit):
        """
        Declines text in line edit by setting red borders
        :param line:
        :return:
        """
        line.setStyleSheet("border: 1px solid red; border-radius: 2px")
        self.doneDict[line] = False

    def enableGenerateButton(self):
        """
		Enables Generate button if all lines are entered
		:return:
		"""
        self.generateButton.setEnabled(
            not bool(False in self.doneDict.values())
        )

    def generate(self):
        # first translate numerical values
        array = [hex((Cmd.CFG_START >> 8 * i) & 0xFF) for i in range(Cmd.SIZE)]
        array += [
            self.to_hex(i)
            for i in [                
                self.signalsNumberSpinBox.value(),
                self.minVoltageSpinBox.value() & 0xFF,
                (self.minVoltageSpinBox.value() >> 8) & 0xFF,
                self.maxVoltageSpinBox.value() & 0xFF,
                (self.maxVoltageSpinBox.value() >> 8) & 0xFF,
                self.updateTimeSpinBox.value(),
            ]
        ]
        # then comes signal names len and value
        for signal in self.signals:
            array.append(hex(len(signal.text())))
            array.extend([hex(ord(char)) for char in signal.text()])

        array = ["\n\t" + i if order % 4 == 0 else i for order, i in enumerate(array)]
        array_final = "{" + ", ".join(value for value in array) + "\n}"

        size = array_final.count("0x")
        self.resultTextBrowser.setText(
            "uint8_t config_size = "
            + str(size)
            + ";\n"
            + "uint8_t config[] = "
            + array_final
            + ";"
        )

    def closeEvent(self, event: QCloseEvent):
        """
        Saves current config settings and accept close event
        :param event:
        :return:
        """
        Settings.byObject(self).lastMinVoltage = self.minVoltageSpinBox.value()
        Settings.byObject(self).lastMaxVoltage = self.maxVoltageSpinBox.value()
        Settings.byObject(self).lastUpdateTime = self.updateTimeSpinBox.value()
        event.accept()

    @staticmethod
    def to_hex(val, nbits=16):
        """
        Analog of hex() but also works for negative
        :param val:
        :param nbits:
        :return:
        """

        return hex((val + (1 << nbits)) % (1 << nbits))
