from pox.core import core
from pox.lib.revent.revent import EventMixin
from extensions.update import UpdateEvent


class Publisher(EventMixin):
    """
  This is a Class for Publisher which can raise an event
  """
    _eventMixin_events = {UpdateEvent}

    def __init__(self):
        self.listenTo(core)
        #print("Publisher is initialed\n")

    def _handle_GoingUpEvent(self, event):
        self.listenTo(core.openflow)
        #print("this is in publisher, what is this for?\n")

    def publishPath(self, flow):
        #print("Voy a lanzar el evento\n")
        self.raiseEvent(UpdateEvent, flow)
        #print("Evento lanzado\n")


def launch():
    core.registerNew(Publisher)
