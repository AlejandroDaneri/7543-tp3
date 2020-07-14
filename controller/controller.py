from pox.core import core
import pox.openflow.discovery
import pox.openflow.spanning_tree
import pox.forwarding.l2_learning
from pox.lib.util import dpid_to_str
from extensions.switch import SwitchController
from extensions.graph import Graph

from extensions.publisher import Publisher

from pox.core import core
from pox.lib.revent import *

log = core.getLogger()

class Controller(EventMixin):

    def __init__(self):
        self.connections = set()
        self.switches = {}
        self.hosts = {}  # host: switch al que se conecto
        self.graph = Graph()
        self.pb = Publisher()

        self.listenTo(core)


        # Esperando que los modulos openflow y openflow_discovery esten listos
        core.call_when_ready(self.startup, ('openflow', 'openflow_discovery'))

    def startup(self):
        """
        Esta funcion se encarga de inicializar el controller
        Agrega el controller como event handler para los eventos de
        openflow y openflow_discovery
        """
        core.openflow.addListeners(self)
        core.openflow_discovery.addListeners(self)

        core.addListeners(self)

        self.listenTo(self.pb)

        log.info('Controller initialized')

    def _handle_ConnectionUp(self, event):
        """
        Esta funcion es llamada cada vez que un nuevo switch establece conexion
        Se encarga de crear un nuevo switch controller para manejar los eventos de cada switch
        """
        log.info("Switch %s has come up.", dpid_to_str(event.dpid))
        self.graph.add_node(dpid_to_str(event.dpid))

        if event.connection not in self.connections:
            self.connections.add(event.connection)
            sw = SwitchController(event.dpid, event.connection, self.graph, self.hosts, self.pb)
            self.switches[dpid_to_str(event.dpid)] = sw

    def _handle_ConnectionDown(self, event):
        if event.connection in self.connections:
            self.connections.remove(event.connection)
        self.graph.remove_node(dpid_to_str(event.dpid))

    def _handle_LinkEvent(self, event):
        """
        Esta funcion es llamada cada vez que openflow_discovery descubre un nuevo enlace
        """
        link = event.link
        src_sw = dpid_to_str(link.dpid1)
        dst_sw = dpid_to_str(link.dpid2)
        src_port = link.port1
        dst_port = link.port2
        log.info("Hosts detectados: %s", self.hosts)
        if event.added:
            try:
                self.graph.add_edge(src_sw, dst_sw)
                self.switches[src_sw].addLinkTo(dst_sw, src_port)
                # ya lo logea el discover pero para testear
                log.info('link added: [%s:%s] -> [%s:%s]', src_sw, src_port, dst_sw, dst_port)
            except:
                log.error("add edge error")
        elif event.removed:
            try:
                self.graph.remove_edge(src_sw, dst_sw)
                self.switches[src_sw].removeLinkTo(dst_sw)
                log.info('link removed [%s:%s] -> [%s:%s]', src_sw, src_port, dst_sw, dst_port)
            except:
                log.error("remove edge error")

    # Capturando el evento de prueba
    def _handle_TestEvent(self, event):
        log.info("Test Event is raised,I heard TestEvent\n")
        flow = event.flow
        path = event.path

        i = 0
        while i < len(path)-1:
            sw_controller = self.switches[path[i]]
            sw_controller.update(flow, path[i+1])

        self.switches[path[i+1]].forwardPortToHost(flow)

def launch():
    # Inicializando el modulo openflow_discovery
    pox.openflow.discovery.launch()

    # Registrando el Controller en pox.core para que sea ejecutado
    core.registerNew(Controller)
