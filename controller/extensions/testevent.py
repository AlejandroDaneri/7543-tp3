from pox.lib.revent.revent import Event


class TestEvent(Event):
    def __init__(self):
        Event.__init__(self)
