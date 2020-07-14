from pox.lib.revent.revent import Event


class TestEvent(Event):
    def __init__(self, flow, path):
        Event.__init__(self)
        self.flow = flow
        self.path = path
