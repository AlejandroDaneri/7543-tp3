from pox.lib.revent.revent import Event


class UpdateEvent(Event):
    def __init__(self, flow):
        Event.__init__(self)
        self.flow = flow