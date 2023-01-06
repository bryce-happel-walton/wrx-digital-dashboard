import can_data_parser
import tomlkit
import can
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget
from inspect import getmembers, isfunction

parsers = {x[0]: x[1] for x in getmembers(can_data_parser, isfunction)}

with open("config/can.toml", "rb") as f:
    config = tomlkit.load(f).unwrap()
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

    def parse_response(self, msg: can.Message) -> None:
        data = msg.data

        if msg.arbitration_id != conversation_ids["response_id"]:
            return
        else:
            expected_bits = data[0]
            service = data[1] - 0x40
            pid = data[2]

            if pid == 0x04:
                print(hex(expected_bits), hex(service), f"{data[3] / 0xFF * 100:.0f}")

    def parse_data(self, msg: can.Message) -> None:
        id = msg.arbitration_id
        data = msg.data

        if id == conversation_ids["response_id"]:
            self.parse_response(msg)
        else:
            for i, v in can_id_items:
                if v == id and i in parsers:
                    self.updated.emit((i, parsers[i](data)))
