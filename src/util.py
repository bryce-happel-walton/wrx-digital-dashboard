def clamp(low, n, high):
    return min(max(n, low), high)


class connection():

    def __init__(self, event, func):
        self.event = event
        self.func = func

    def disconnect(self):
        self.event.connections.pop(self.func)


class event():

    connections = {}

    def connect(self, func) -> connection:
        self.connections[func] = func
        return connection(self, len(self.connections))

    def emit(self, *args, **kwargs):
        for v in self.connections:
            self.connections[v](*args, **kwargs)
