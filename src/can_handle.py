import can_data_parser, tomllib, can
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget
from inspect import getmembers, isfunction

parsers = {x[0]: x[1] for x in getmembers(can_data_parser, isfunction)}

with open("config/can.toml", "rb") as f:
    config = tomllib.load(f)
    can_ids = config["can_ids"]
    conversation_ids = config["conversation_ids"]

can_id_items = can_ids.items()
can_id_values = can_ids.values()


class CanApplication(QWidget):

    updated = pyqtSignal(tuple)
    response_recieved = pyqtSignal()

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
            self.response_recieved.emit()
            # print("Received: ", hex(id), [hex(x) for x in list(data)])

            # if data[2] == 0x08:
            #     page = data[0]
            #     length = data[1]
            # elif data[1] == 0x08:
            #     length = data[0]
        else:
            for i, v in can_id_items:
                if v == id and i in parsers:
                    self.updated.emit((i, parsers[i](data)))
