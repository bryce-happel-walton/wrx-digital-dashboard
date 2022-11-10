import can


class CanApplication():

    def __init__(self):
        self.bus = can.interface.Bus(channel='can0',
                                     bustype='socketcan',
                                     bitrate=500000)

    def printout(self):
        notifier = can.Notifier(self.bus, [can.Printer()])
