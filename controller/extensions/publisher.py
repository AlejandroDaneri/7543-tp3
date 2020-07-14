from pox.core import core
from pox.lib.revent.revent import EventMixin
from extensions.testevent import TestEvent


class Publisher(EventMixin):
    """
  This is a Class for Publisher which can raise an event
  """
    _eventMixin_events = {TestEvent}

    def __init__(self):
        self.listenTo(core)
        print("Publisher is initialed\n")

    def _handle_GoingUpEvent(self, event):
        self.listenTo(core.openflow)
        print("this is in publisher, what is this for?\n")

    def publishPath(self, flow, path):
        print("Voy a lanzar el evento\n")
        self.raiseEvent(TestEvent, flow, path)
        print("Evento lanzado\n")


def launch():
    core.registerNew(Publisher)
