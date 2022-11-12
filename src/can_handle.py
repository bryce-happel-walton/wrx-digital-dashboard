import can
import can_data

from util import event
from inspect import getmembers, isfunction

can_ids = {
    'left_sw_stock': 0x152,
    'throttle_pedal': 0x140,
    'vehicle_speed': 0x0D1,
    'wheel_speeds': 0x0D4,
    'door_states': 0x375,
    'steering_wheel_position': 0x002,
    'climate_control': 0x281,
    'rpm': 0x141
}

parsers = {x[0]: x[1] for x in getmembers(can_data, isfunction)}

can_id_keys = list(can_ids.keys())
can_id_values = list(can_ids.values())


def get_can_index(id: int):
    if not id in can_id_values:
        return None
    return can_id_keys[can_id_values.index(id)]


class CanApplication():

    updated = event()

    def __init__(self) -> None:
        self.bus = can.interface.Bus(channel='can0',
                                bustype='socketcan',
                                bitrate=500000)

    def get_data(self):
        return self.bus.recv(1)

    def parse_data(self, msg: can.Message) -> None:
        id = msg.arbitration_id
        data = msg.data

        can_str_id = get_can_index(id)
        if can_str_id in parsers:
            self.updated.emit(can_str_id, parsers[can_str_id](data))


if __name__ == "__main__":
    import subprocess
    import platform

    if platform != "Linux":
        pass
        exit()

    try:
        shutdown_can = subprocess.run(
            ["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
        setup_can = subprocess.run([
            "sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can",
            "bitrate", "500000"
        ],
                                   check=True)
        can_app = CanApplication()
    except:
        print("Could not find PiCan device! Quitting.")
        exit()

    while True:
        msg = can_app.get_data()

        if msg is not None:
            can_app.parse_data(msg)
