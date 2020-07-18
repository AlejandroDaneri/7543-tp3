import pox.openflow.discovery
from pox.lib.util import dpid_to_str
from extensions.switch import SwitchController
#from extensions.graph import Graph
from extensions.dijkstra import find_all_paths
from networkx import Graph, all_shortest_paths


from pox.core import core
from pox.lib.revent import *

log = core.getLogger()

class Controller(EventMixin):

    def __init__(self):
        self.connections = set()
        self.switches = {}
        self.hosts = {}  # host: switch al que se conecto
        self.graph = Graph()
        self._ecmp_last_index_used = {}
        # Esperando que los modulos openflow ,openflow_discovery y host_tracker esten listos
        core.call_when_ready(self.startup, ('openflow', 'openflow_discovery', 'host_tracker'))

    def get_hosts(self):
        return self.hosts

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
        core.openflow.addListenerByName("FlowRemoved", self._handle_flow_removal)

        log.info('Controller initialized')

    def _handle_ConnectionUp(self, event):
        """
        Esta funcion es llamada cada vez que un nuevo switch establece conexion
        """
        log.info("Switch %s has come up.", dpid_to_str(event.dpid))
        self.graph.add_node(dpid_to_str(event.dpid))

        if event.connection not in self.connections:
            self.connections.add(event.connection)
            sw = SwitchController(event.dpid, event.connection, self)
            self.switches[dpid_to_str(event.dpid)] = sw

    def _handle_ConnectionDown(self, event):
        if event.connection in self.connections:
            self.connections.remove(event.connection)
        self.graph.remove_node(dpid_to_str(event.dpid))

    def _handle_flow_removal(self, event):
        flow_removed = event.ofp
        log.debug("Flow removed %s " % str(flow_removed))
        for sw in self.switches:
            self.switches[sw].removeRuleByFlow(flow_removed)

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
                log.info('link added: [%s:%s] -> [%s:%s]', src_sw, src_port, dst_sw, dst_port)
            except:
                log.error("add edge error")
        elif event.removed:
            try:
                self.graph.remove_edge(src_sw, dst_sw)
                self.switches[src_sw].removeLinkTo(dst_sw)
                log.info('link removed [%s:%s] -> [%s:%s]', src_sw, src_port, dst_sw, dst_port)
            except Exception as e:
                log.error("remove edge error: %s" % str(e))

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
    def _find_path(self, flow):
        # all_paths = [shortest_path(self.graph, str(flow.src_hw), str(flow.dst_hw))]
        #all_paths = find_all_paths(self.graph, str(flow.src_hw), str(flow.dst_hw))
        all_paths = []
        all_paths.extend(all_shortest_paths(self.graph, str(flow.src_hw), str(flow.dst_hw)))

        if not all_paths:
            log.debug("No se pudo identificar un path entre %s y %s" % (str(flow.src_hw), str(flow.dst_hw),))
            return None
        index = self._get_latest_ECMP_index(str(flow.src_hw), str(flow.dst_hw), len(all_paths))
        path = all_paths[index]
        return path

    # Instalo las reglas que matcheen con el flow especifico para todos los switches del path
    def install(self, flow):
        path = self._find_path(flow)
        if path is None:
            return False
        i = 0
        while i < len(path):
            log.debug("Estoy en el loop instalando reglas", i)
            if path[i] in self.switches:
                sw_controller = self.switches[path[i]]
                next_hop = None if i == len(path) - 1 else path[i + 1]
                sw_controller.update(flow, next_hop)
            i += 1
        return True

    def _handle_HostEvent(self, event):
        h = str(event.entry.macaddr)
        s = dpid_to_str(event.entry.dpid)
        p = event.entry.port

        log.debug("Event mac: %s,  switch %s, IP: %s" % (h, s, event.entry.ipAddrs))
        log.debug("Hosts detectados: %s", self.hosts)
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
    launch(arpSilent=45)

    # Registrando el Controller en pox.core para que sea ejecutado
    core.registerNew(Controller)
