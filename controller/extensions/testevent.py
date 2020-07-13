from pox.lib.revent.revent import Event


class TestEvent(Event):
    def __init__(self, arg1):
        Event.__init__(self)
        self.arg1 = arg1
