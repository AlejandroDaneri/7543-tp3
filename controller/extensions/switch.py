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
    # "CAM table", con pares (MAC-addr, port)
    self.table = {}

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
      log.info("[%s puerto %s] %s -> %s", dpid_to_str(event.dpid), event.port, ip.srcip, ip.dstip)

      #Actualizo la tabla
      self.table[packet.src] = event.port

      dst_port = self.table.get(packet.dst)

      # Esto no se si deberia estar aca
      # Si a un switch le llega un paquete desde un host que NO ha sido registrado en la red entonces
      # lo registra como conectado a ese switch, ya que al ser el primero en detectarlo es el que esta
      # directamente conectado
      if ip.srcip not in self.hosts:
        self.hosts[ip.srcip] = dpid_to_str(event.dpid)

      # Hardcodeo de prueba, para saber magicamente el switch de h7 cuando hago X--ping->h7 en topo de 3 lvls
      if (ip.dstip == '10.0.0.7') or (ip.srcip in self.hosts):
        dest = '00-00-00-00-00-07'

        if ip.dstip != '10.0.0.7':
          dest = self.hosts[ip.dstip]
        print("El camino minimo es:", shortest_path(self.graph, self.hosts[ip.srcip], dest))

        path = shortest_path(self.graph, self.hosts[ip.srcip], dest)

        # Lanzo evento para crear las reglas en todos los switches del camino (incluido este)
        flow = Flow(ip.srcip, 80, ip.dstip, 80, ip.protocol, packet)
        self.pb.publishPath(flow, path)


        # Reenvio el paquete que genero el packetIn sacandolo por el puerto que matchea con la nueva regla
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=of.OFPP_TABLE))
        self.connection.send(msg)

  def update(self, flow, next_sw):
    msg = of.ofp_flow_mod()
    msg.match.dl_src = flow.packet.src
    msg.match.dl_dst = flow.packet.dst
    port = self.neighbour[next_sw]
    print("update", self.dpid, port)
    msg.actions.append(of.ofp_action_output(port=port))
    self.connection.send(msg)

  def addLinkTo(self, dst_sw, src_port):
    self.neighbour[dst_sw] = src_port

  def removeLinkTo(self, dst_sw):
    del self.neighbour[dst_sw]

  #harcodeado
  def forwardPortToHost(self, flow):
    msg = of.ofp_flow_mod()
    msg.match.dl_src = flow.packet.src
    msg.match.dl_dst = flow.packet.dst
    print("forward", self.dpid)

    # Si va hacia el 10.0.0.7 se que tiene que salir por puerto 3, si vuelve hacia 10.0.0.1 por puerto 1, 10.0.0.2 al 2.. etc
    port = 3 if flow.packet.find('ipv4').dstip == '10.0.0.7' else int(flow.packet.find('ipv4').dstip.toStr().split('.')[-1])
    msg.actions.append(of.ofp_action_output(port=port))
    self.connection.send(msg)



