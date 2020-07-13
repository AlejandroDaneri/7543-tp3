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
        print("Publisher is intialed\n")

    def publishEvent(self):
        print("publishEvent is called, will raise the test Event\n")
        self.raiseEvent(TestEvent, "firstPar", "secondPar")
        print("foo raised event\n")


def launch():
    core.registerNew(Publisher)
