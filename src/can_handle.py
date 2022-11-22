import can
import can_data

from util import event
from inspect import getmembers, isfunction

can_ids = {
    'turn_signals': 0x282,

    'vehicle_speed': 0x0D1,
    'brake_pedal_position': 0x0D1,

    'wheel_speeds': 0x0D4,

    #'door_states': 0x375,
    #'steering_wheel_position': 0x002,
    #'climate_control': 0x281,

    'coolant_temp': 0x360,
    'oil_temp': 0x360,

    'throttle_pedal_position': 0x140,
    'throttle_plate_position': 0x140,

    'headlights': 0x152,
    'handbrake': 0x152,
    'reverse_switch': 0x152,
    'brake_switch': 0x152,

    'clutch_switch': 0x144,

    'rpm': 0x141,
    'neutral_switch': 0x141
}

parsers = {x[0]: x[1] for x in getmembers(can_data, isfunction)}

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

        for i, v in can_ids.items():
            if v == id and i in parsers:
                self.updated.emit(i, parsers[i](data))


if __name__ == "__main__":
    import subprocess
    import platform

    if platform != "Linux":

        def parse_test(msg):
            id = msg.arbitration_id
            data = msg.data

            for i, v in can_ids.items():
                if v == id and i in parsers:
                    print(i, parsers[i](data))

        # parse_test(
        #     can.Message(arbitration_id=0x141,
        #                 data=bytearray(
        #                     [0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00])))

        for i, v in can_ids.items():
            if i in parsers:
                print(i)

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
            print(can_app.parse_data(msg))
