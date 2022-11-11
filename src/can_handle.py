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
        message = self.bus.recv()

        return message


if __name__ == "__main__":
    import subprocess

    try:
        shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
        setup_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)
        can = CanApplication()
    except:
        print("Could not find PiCan device! Quitting.")
        exit()


    while True:
        data = can.get_data()

        if data:
            print(data.data)




