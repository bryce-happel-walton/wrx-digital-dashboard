from time import perf_counter
from inspect import getmembers, isfunction
from typing import Any
import cantools
import tomlkit
import can
from PyQt5 import QtCore, QtWidgets
from qutil import timed_func
from data import CarData
import can_data_parser

parsers = {x[0]: x[1] for x in getmembers(can_data_parser, isfunction)}


with open("config/can.toml", "rb") as f:
    CONFIG: dict[str, Any] = tomlkit.load(f).unwrap()
    CAN_IDS: dict[str, int] = CONFIG["can_ids"]
    CONVERSATION_IDS: dict[str, int] = CONFIG["conversation_ids"]
    CURRENT_DATA_DEFINITIONS: dict[str, dict[str, int]] = CONFIG[
        "current_data_mode_definitions"
    ]
    MODE_IDS: dict[str, int] = CONFIG["mode_ids"]


CONVERSATION_WAIT = 2
CONVERSATION_PERIOD_MS = 50

MODE_OFFSET = 0x40

CAN_ID_ITEMS = CAN_IDS.items()
CAN_ID_VALUES = CAN_IDS.values()
CURRENT_DATA_DEFINITION_KEYS = list(CURRENT_DATA_DEFINITIONS.keys())
CURRENT_DATA_DEFINITION_ITEMS = CURRENT_DATA_DEFINITIONS.items()

NUM_DEFINITIONS = len(CURRENT_DATA_DEFINITIONS)

CAN_FILTER = [
    {"can_id": x, "can_mask": 0xFFF, "extended": False} for x in CAN_ID_VALUES
]

for x in CURRENT_DATA_DEFINITIONS.values():
    CAN_FILTER.append({"can_id": x, "can_mask": 0xFFF, "extended": False})


wrx_can_db = cantools.db.load_file("resources/database/subaru_wrx_2018.dbc")

DECODABLE_IDS = []
for db_msg in wrx_can_db.messages:
    DECODABLE_IDS.append(db_msg.frame_id)


class CanHandler(QtWidgets.QWidget):

    updated = QtCore.pyqtSignal(tuple)
    conversation_timer = QtCore.QTimer()

    def __init__(self, parent: QtWidgets.QApplication, bus: can.interface.Bus) -> None:
        super().__init__()
        self.bus = bus
        self.q_app = parent
        self.car_data = CarData()
        self.conversation_response_debounce = True
        self.last_conversation_response_time = perf_counter() * 1000
        self.conversation_list_index = 0
        self.last_mode_sent = 0
        self.last_pid_sent = 0

        self.bus.set_filters(CAN_FILTER)

        self.can_notifier = can.notifier.Notifier(self.bus, [self.parse_data])
        # timed_func(self.qApp, self.run_conversation, 1)

    def stop(self) -> None:
        self.can_notifier.stop()
        self.bus.shutdown()

    def send(self, msg: can.message.Message) -> None:
        msg.is_extended_id = False
        self.bus.send(msg)

    def run_conversation(self) -> None:
        current_time = perf_counter() * 1000
        if self.conversation_response_debounce:
            self.last_conversation_response_time = current_time
            self.conversation_response_debounce = False

            definition_index = CURRENT_DATA_DEFINITION_KEYS[
                self.conversation_list_index
            ]
            definition = CURRENT_DATA_DEFINITIONS[definition_index]

            data = [0x55 for _ in range(8)]
            data[0] = definition["sent_bytes"]
            data[1] = MODE_IDS["current_data"]
            data[2] = definition["pid"]

            message = can.message.Message(
                arbitration_id=CONVERSATION_IDS["send_id"], data=data
            )

            self.last_mode_sent = data[1]
            self.last_pid_sent = data[2]

            self.send(message)

            self.conversation_list_index += 1
            if self.conversation_list_index >= NUM_DEFINITIONS:
                self.conversation_list_index = 0
        elif (
            current_time - self.last_conversation_response_time
            >= CONVERSATION_PERIOD_MS
        ):
            print(
                f"[Warning] No response to last PID [{hex(self.last_pid_sent)}]. Continuing anyway."
            )
            self.conversation_response_debounce = True
            self.last_conversation_response_time = current_time

    # TODO: used buffered reader for better handling of detecting other devices, and conversations
    def parse_response(self, msg: can.message.Message) -> None:
        # TODO: handle more expected bits and multiple messages
        data = msg.data
        expected_bits = data[0]
        mode = data[1] - MODE_OFFSET
        pid = data[2]

        if expected_bits > 8:
            print(
                "[Error] Unexpected long message. Currently unable to process this message."
            )
            return

        if mode == self.last_mode_sent and pid == self.last_pid_sent:
            self.conversation_response_debounce = True

        for i, v in CURRENT_DATA_DEFINITION_ITEMS:
            if i in parsers and v["pid"] == pid:
                necessary_data = data[3 : 3 + v["response_length"]]
                self.updated.emit((i, parsers[i](necessary_data)))

    def parse_data(self, msg: can.message.Message) -> None:
        msg_id = msg.arbitration_id
        msg_data = msg.data

        if msg_id == CONVERSATION_IDS["ecu_response_id"]:
            self.parse_response(msg)
        elif msg_id in DECODABLE_IDS:
            decode = wrx_can_db.decode_message(msg_id, msg_data)
            for msg in decode:
                db_msg_name, val = msg, decode[msg]
                setattr(self.car_data, db_msg_name, val)
                self.updated.emit((db_msg_name, val))
        else:
            for db_msg_name, db_msg_id in CAN_ID_ITEMS:
                if db_msg_name in parsers and db_msg_id == msg_id:
                    val = parsers[db_msg_name](msg_data)
                    setattr(self.car_data, db_msg_name, val)
                    self.updated.emit((db_msg_name, val))
