import can

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


class CanApplication():

    def __init__(self):
        self.bus = can.interface.Bus(channel='can0',
                                     bustype='socketcan',
                                     bitrate=500000)

    def get_data(self):
        message = self.bus.recv(1)

        return message

    def parse_data(self, msg: can.Message):
        id = msg.arbitration_id
        data = msg.data

        if id == can_ids["rpm"]:
            v = int.from_bytes(data[0])

            print(v)


if __name__ == "__main__":
    import subprocess

    try:
        shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
        setup_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)
        can_app = CanApplication()
    except:
        print("Could not find PiCan device! Quitting.")
        exit()

    while True:
        msg = can_app.get_data()

        if msg is not None:
            can_app.parse_data(msg)

