import can_data_parser
import tomllib
import can
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget
from inspect import getmembers, isfunction

parsers = {x[0]: x[1] for x in getmembers(can_data_parser, isfunction)}

with open("config/can.toml", "rb") as f:
    config = tomllib.load(f)
    can_ids = config["can_ids"]
    conversation_ids = config["conversation_ids"]


class CanApplication(QWidget):

    updated = pyqtSignal(tuple)

    def __init__(self, qApp: QApplication, bus: can.interface.Bus) -> None:
        super().__init__()
        self.bus = bus
        self.qApp = qApp

    def send(self, msg: can.Message) -> None:
        self.bus.send(msg)

    @pyqtSlot(can.Message)
    def parse_data(self, msg: can.Message) -> None:
        id = msg.arbitration_id
        data = msg.data

        if id == conversation_ids["response_id"]:
            pass
            # print("Received: ", hex(id), [hex(x) for x in list(data)])

            # if data[1] == 0x08:
            #     length = data[0]
            # elif data[2] == 0x08:
            #     page = data[0]
            #     length = data[1]
        else:
            for i, v in can_ids.items():
                if v == id and i in parsers:
                    self.updated.emit((i, parsers[i](data)))
