from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from extensions.flow import Flow
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.udp import udp
from pox.lib.packet.tcp import tcp

log = core.getLogger()

class SwitchController:
  def __init__(self, dpid, connection,  hosts,pb):
    self.dpid = dpid_to_str(dpid)
    self.connection = connection
    # El SwitchController se agrega como handler de los eventos del switch
    self.connection.addListeners(self)
    self.pb = pb
    self.hosts = hosts

    # switch_vecino: puerto para llegar
    self.neighbour = {}

  def _handle_PacketIn(self, event):
    """
    Esta funcion es llamada cada vez que el switch recibe un paquete
    y no encuentra en su tabla una regla para rutearlo
    """
    packet = event.parsed
    src_port = None
    dst_port = None
    ip = None
    if isinstance(packet.next, ipv4):
      ip = packet.next
      if isinstance(ip.next, tcp) or isinstance(ip.next, udp):
        src_port = ip.next.srcport
        dst_port = ip.next.dstport

    if ip:
      log.info("[%s puerto %s] %s (%s) -> %s (%s)", dpid_to_str(event.dpid), event.port, ip.srcip, str(packet.src),
               ip.dstip, str(packet.dst))

      # Identifico el Flow en base a IPs, Puertos y Protocolo
      flow = Flow(ip.srcip, src_port, ip.dstip, dst_port, ip.protocol, packet.src, packet.dst)
      self.pb.publishPath(flow)

      # Reenvio el paquete que genero el packetIn sacandolo por el puerto que matchea con la nueva regla
      msg = of.ofp_packet_out()
      msg.data = event.ofp
      msg.actions.append(of.ofp_action_output(port=of.OFPP_TABLE))
      self.connection.send(msg)
    else:
      log.info("Ignorando [%s puerto %s] (%s) -> (%s)", dpid_to_str(event.dpid), event.port, str(packet.src),
               str(packet.dst))


  def update(self, flow, next_hop, ip_routing=True):
    msg = of.ofp_flow_mod()
    if not ip_routing:
      # Aplicon Routing a nivel L2, solamente considerando mac addresses
      # Esto no me permite implementar ECMP porque siempre van a ir de un src a un dst
      # por el mismo lugar
      msg.match.dl_src = flow.src_hw
      msg.match.dl_dst = flow.dst_hw
    else:
      print("Protocol: %s" % str(flow.protocol))

      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.match.nw_dst = flow.dst_ip
      msg.match.nw_src = flow.src_ip

      if (flow.protocol == pkt.ipv4.TCP_PROTOCOL) or (flow.protocol == pkt.ipv4.UDP_PROTOCOL):
        msg.match.nw_proto = flow.protocol
        msg.match.tp_dst = flow.dst_port
        msg.match.tp_src = flow.src_port

    if next_hop in self.neighbour:
      port = self.neighbour[next_hop]
      print("update", self.dpid, port)
    else:
      port = self.hosts[str(flow.dst_hw)]
      print("forward", self.dpid)
    msg.actions.append(of.ofp_action_output(port=port))
    self.connection.send(msg)

  def addLinkTo(self, dst_sw, src_port):
    self.neighbour[dst_sw] = src_port

  def removeLinkTo(self, dst_sw):
    self.removeRuleTo(self.neighbour[dst_sw])
    del self.neighbour[dst_sw]

  def removeRuleTo(self, out_port):
    print("Eliminando")
    msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    msg.out_port = out_port
    self.connection.send(msg)


