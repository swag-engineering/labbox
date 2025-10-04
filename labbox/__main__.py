import sys
from PyQt5 import QtWidgets

from labbox.LabBox import LabBox
from labbox.Settings import Settings


def main():
    app = QtWidgets.QApplication(sys.argv)

    if sys.platform != "linux":
        app.setStyle(Settings.defaultStyle)

    ui = LabBox()
    ui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
