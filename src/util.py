class connection():

    def __init__(self, event, i):
        self.event = event
        self.index = i

    def disconnect(self):
        self.event.connections.pop(self.index)


class event():

    connections = []

    def connect(self, func) -> connection:
        self.connections.append(func)
        return connection(self, len(self.connections))

    def emit(self, *args, **kwargs):
        for v in self.connections:
            v(*args, **kwargs)
