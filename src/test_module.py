from typing import Callable
import can_handle
import can
from random import choice, randrange
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot, QPoint
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QLabel,
    QMainWindow,
    QFrame,
    QCheckBox,
    QSlider,
    QTextEdit,
    QRadioButton,
)

# todo: make testing UI with controls for everything

turn_signal_data = [
    0x30,  # hazards
    0x20,  # right turn
    0x10,  # left turn
    0x00,  # everything off
]


def provide_random_message() -> can.Message:
    key, val = choice(list(can_handle.can_ids.items()))
    data = [0, 0, 0, 0, 0, 0, 0, 0]
    if key in ["turn_signals", "fuel_level"]:
        data = [randrange(0x25, 0xFF), 0, 0, 0, 0, choice(turn_signal_data), 0, 0]
    elif key in [
        "oil_temp",
        "coolant_temp",
        "cruise_control_speed",
        "cruise_control_status",
        "cruise_control_set",
    ]:
        data = [
            0,
            0,
            randrange(0, int((0xFA - 32) / 1.8)),
            randrange(0, int((0xFA - 32) / 1.8)),
            0,
            int(f"00{randrange(0,2)}{randrange(0,2)}0000", 2),
            0,
            randrange(0, 256),
        ]
    elif key in ["headlights", "handbrake_switch", "reverse_switch", "brake_switch"]:
        data = [
            0,
            0,
            0,
            0,
            0,
            0,
            int(f"00{randrange(0,2)}0{randrange(0,2)}000", 2),
            choice([0x8C, 0x80, 0x98, 0x9C, 0x84, 0x82]),
        ]
    elif key == "door_states":
        data = [
            0,
            int(
                f"00{randrange(0,2)}0{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}",
                2,
            ),
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    elif key in ["rpm", "neutral_switch"]:
        data = [0, 0, 0, 0, randrange(0, 256), randrange(0, 256), choice([27, 20]), 0]
    elif key in ["vehicle_speed", "brake_pedal_position"]:
        data = [0, randrange(0, 180 // 14 + 1), 0, 0, 0, 0, 0, 0]
    elif key == "clutch_switch":
        data = [0, int(f"{randrange(0,2)}0000000", 2), 0, 0, 0, 0, 0, 0]
    elif key == "traction_control":
        data = [0, int(f"0000{randrange(0,2)}000", 2), 0, 0, 0, 0, 0, 0]
    elif key == "traction_control_mode":
        data = [int(f"0000{randrange(0,2)}000", 2), 0, 0, 0, 0, 0, 0, 0]
    elif key == "seatbelt_driver":
        data = [0, 0, 0, 0, 0, int(f"0000000{randrange(0,2)}", 2), 0, 0]
    elif key == "fog_lights":
        data = [0, int(f"0{randrange(0,2)}000000", 2), 0, 0, 0, 0, 0, 0]

    return can.Message(is_extended_id=False, arbitration_id=val, data=data)


def provide_response_message(recv_msg: can.Message) -> can.Message | list[can.Message]:
    if recv_msg.arbitration_id == can_handle.conversation_ids["send_id"]:
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        return can.Message(
            is_extended_id=False,
            arbitration_id=can_handle.conversation_ids["response_id"],
            data=data,
        )


WINDOW_SIZE = [750, 720]
H_BUFFER = QPoint(10, 0)
V_BUFFER = QPoint(0, 10)
ITEM_BUFFER = QPoint(0, 0)


class TestController(QMainWindow):

    data_changed = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, canbus: can.interface.Bus) -> None:
        super().__init__()

        self.canbus = canbus
        self.data: dict[int, list[list[str]]] = {}

        self.setFixedSize(*WINDOW_SIZE)

        self.selection_frame = QFrame(self)
        self.slider_frame = QFrame(self)
        self.val_frame = QFrame(self)

        self.selection_frame.resize(
            WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] - WINDOW_SIZE[1] // 3
        )
        self.slider_frame.resize(WINDOW_SIZE[0], WINDOW_SIZE[1] // 3)
        self.val_frame.resize(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] - WINDOW_SIZE[1] // 3)

        self.selection_frame.move(0, WINDOW_SIZE[1] // 3)
        self.val_frame.move(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 3)

        self._current_switch_height = QPoint(0, 0)

        self.make_selections()
        self.make_sliders()
        self.make_vals()

        self.data_changed.connect(self.write_data)

        self.show()

    def write_data(self) -> None:
        for id, data in self.data.items():
            new_data = [int("".join(x), 2) for x in data]
            self.canbus.send(
                can.Message(is_extended_id=False, arbitration_id=id, data=new_data)
            )

    def update_addr_bool(self, id: int, byte: int, bit: int, value: bool) -> None:
        if not id in self.data:
            self.data[id] = [["0" for _ in range(8)] for _ in range(8)]

        self.data[id][byte][bit] = str(int(value))
        print(hex(id), byte, bit, self.data[id][byte])
        self.data_changed.emit()

    def bind_switch(self, id: int, byte: int, bit: int) -> Callable:
        return lambda state: self.update_addr_bool(id, byte, bit, state)

    def add_switch(
        self, label: str, id: int, byte: int, bit: int, callable: Callable | None = None
    ) -> QCheckBox:
        switch = QCheckBox(label, self.selection_frame)
        switch.adjustSize()
        switch.move(self.selection_frame.pos() + H_BUFFER + self._current_switch_height)
        if callable:
            switch.toggled.connect(callable)
        else:
            switch.toggled.connect(self.bind_switch(id, byte, bit))
        self._current_switch_height += QPoint(0, switch.height()) + ITEM_BUFFER
        return switch

    def make_selections(self) -> None:
        self.add_switch("Clutch: ", 0x140, 1, 0)
        cruise_control_switch = self.add_switch("Cruise control: ", 0x360, 5, 3)
        cruise_control_switch.toggled.connect(
            lambda state: self.update_addr_bool(0x360, 5, 2, 0) if not state else None
        )

    def make_sliders(self) -> None:
        pass

    def make_vals(self) -> None:
        pass

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)
