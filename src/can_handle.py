import can


class CanApplication():

    def __init__(self):
        self.bus = can.interface.Bus(channel='can0',
                                     bustype='socketcan',
                                     bitrate=500000)

    def printout(self):
        can.Notifier(self.bus, [can.Printer()])


if __name__ == "__main__":
    import subprocess

    try:
        shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
        setup_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)
    except:
        print("Could not find PiCan device! Quitting.")

    can_app = CanApplication()
    can_app.printout()
