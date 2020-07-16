from pox.core import core
import pox.openflow.discovery
import pox.openflow.spanning_tree
import pox.forwarding.l2_learning
from pox.lib.util import dpid_to_str
from extensions.switch import SwitchController
from extensions.graph import Graph
from pox.host_tracker import host_tracker
from extensions.publisher import Publisher
from extensions.dijkstra import shortest_path

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
        self._ecmp_last_index_used = {}
        # Esperando que los modulos openflow y openflow_discovery esten listos
        core.call_when_ready(self.startup, ('openflow', 'openflow_discovery', 'host_tracker'))

    def startup(self):
        """
        Esta funcion se encarga de inicializar el controller
        Agrega el controller como event handler para los eventos de
        openflow y openflow_discovery
        """
        core.openflow.addListeners(self)
        core.openflow_discovery.addListeners(self)
        core.host_tracker.addListeners(self)
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
            sw = SwitchController(event.dpid, event.connection, self.hosts, self.pb)
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

    def _get_latest_ECMP_index(self, src, dst, total):
        if (src, dst) not in self._ecmp_last_index_used:
            self._ecmp_last_index_used[(src, dst)] = 0
        else:
            if self._ecmp_last_index_used[(src, dst)] == total - 1:
                self._ecmp_last_index_used[(src, dst)] = 0
            else:
                self._ecmp_last_index_used[(src, dst)] += 1
        return self._ecmp_last_index_used[(src, dst)]

    # Calcula el ECMP adecuado e instala la ruta de L2 entre el Host origen y el destino
    def _handle_UpdateEvent(self, event):
        flow = event.flow

        # TODO the following method should return ALL possible shortest paths and not just one.
        all_paths = [shortest_path(self.graph, str(flow.src_hw), str(flow.dst_hw))]
        # TODO END of code that needs to change

        index = self._get_latest_ECMP_index(str(flow.src_hw), str(flow.dst_hw), len(all_paths))
        path = all_paths[index]

        i = 0
        while i < len(path):
            print("Estoy en el loop", i)
            if path[i] in self.switches:
                sw_controller = self.switches[path[i]]
                next_hop = None if i == len(path) - 1 else path[i + 1]
                sw_controller.update(flow, next_hop)
            i += 1

    def _handle_HostEvent(self, event):
        h = str(event.entry.macaddr)
        s = dpid_to_str(event.entry.dpid)
        p = event.entry.port
        i = None
        if len(event.entry.ipAddrs):
            i = event.entry.ipAddrs[0]
        log.info("Event mac: %s,  switch %s, IP: %s" % (h, s, event.entry.ipAddrs))
        log.info("Hosts detectados: %s", self.hosts)
        if event.leave:
            if h in self.hosts:
                del self.hosts[h]
            if h in self.graph.nodes():
                self.graph.remove_node(h)
        else:
            if h not in self.hosts:
                self.hosts[h] = p
            if h not in self.graph.nodes():
                self.graph.add_node(h)
                self.graph.add_edge(h, s)
                self.graph.add_edge(s, h)


def launch():
    # Inicializando el modulo openflow_discovery
    pox.openflow.discovery.launch()
    from host_tracker import launch
    launch()

    # Registrando el Controller en pox.core para que sea ejecutado
    core.registerNew(Controller)
