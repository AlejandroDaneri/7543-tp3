from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt  # POX convention
from extensions.dijkstra import shortest_path
from extensions.flow import Flow

log = core.getLogger()

class SwitchController:
  def __init__(self, dpid, connection, graph, hosts,pb):
    self.dpid = dpid_to_str(dpid)
    self.connection = connection
    # El SwitchController se agrega como handler de los eventos del switch
    self.connection.addListeners(self)
    self.pb = pb
    self.graph = graph
    self.hosts = hosts

    # switch_vecino: puerto para llegar
    self.neighbour = {}

  def _handle_PacketIn(self, event):
    """
    Esta funcion es llamada cada vez que el switch recibe un paquete
    y no encuentra en su tabla una regla para rutearlo
    """
    packet = event.parsed
    ip = packet.find('ipv4')
    if ip:
      log.info("[%s puerto %s] %s (%s) -> %s (%s)", dpid_to_str(event.dpid), event.port, ip.srcip,str(packet.src),
               ip.dstip, str(packet.dst))
      path = shortest_path(self.graph, str(packet.src), str(packet.dst))
      print("El camino minimo es:", path)

      # Lanzo evento para crear las reglas en todos los switches del camino (incluido este)
      flow = Flow(ip.srcip, 80, ip.dstip, 80, ip.protocol, packet)
      self.pb.publishPath(flow, path)

      # Reenvio el paquete que genero el packetIn sacandolo por el puerto que matchea con la nueva regla
      msg = of.ofp_packet_out()
      msg.data = event.ofp
      msg.actions.append(of.ofp_action_output(port=of.OFPP_TABLE))
      self.connection.send(msg)

  def update(self, flow, next_hop):
    msg = of.ofp_flow_mod()
    msg.match.dl_src = flow.packet.src
    msg.match.dl_dst = flow.packet.dst
    if next_hop in self.neighbour:
      port = self.neighbour[next_hop]
      print("update", self.dpid, port)
    else:
      port = self.hosts[str(flow.packet.dst)]
      print("forward", self.dpid)
    msg.actions.append(of.ofp_action_output(port=port))
    self.connection.send(msg)

  def addLinkTo(self, dst_sw, src_port):
    self.neighbour[dst_sw] = src_port

  def removeLinkTo(self, dst_sw):
    del self.neighbour[dst_sw]


