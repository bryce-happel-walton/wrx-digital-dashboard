import can_data
import tomllib
import can
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget
from inspect import getmembers, isfunction

can_ids = {}
parsers = {x[0]: x[1] for x in getmembers(can_data, isfunction)}

with open("config/can.toml", "rb") as f:
    config = tomllib.load(f)
    for i, v in config["can_ids"].items():
        can_ids[i] = int(v, base=16)


class CanApplication(QWidget):

    updated = pyqtSignal(tuple)

    def __init__(self, qApp: QApplication, bus: can.interface.Bus) -> None:
        super().__init__()
        self.bus = bus
        self.qApp = qApp

    @pyqtSlot(can.Message)
    def parse_data(self, msg: can.Message) -> None:
        id = msg.arbitration_id
        data = msg.data

        if id == 0x144:
            print(data)

        for i, v in can_ids.items():
            if v == id and i in parsers:
                self.updated.emit((i, parsers[i](data)))
