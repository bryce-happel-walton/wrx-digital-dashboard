import can
import can_data
import tomllib

from util import event
from inspect import getmembers, isfunction

can_ids = {}

with open("config/can.toml", "rb") as f:
    config = tomllib.load(f)
    for i, v in config["can_ids"].items():
        can_ids[i] = int(v, base=16)

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
