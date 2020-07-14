from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
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
        # next_sw = path.popleft()

        # Intentando hacer lo que dice (1)
        flow = Flow(ip.srcip, 80, ip.dstip, 80, ip.protocol)
        self.pb.publishPath(flow, path)

        # (1) Lo que sigue deberia mandarse para guardar en todos los switches del path
        # porque de esta forma no funciona
        # EJ: path (00-01,00-02, 00-07) y suponiendo que de s1 a s2 voy por puerto 3 y de s2 a s7,puerto 5
        # entonces, decirle al s1 que el paquete con tal ip_src y tal ip_dest vaya puerto 3
        # s2 con ese mismo ip_src y ip_dest vaya por puerto 5 ,etc

        # Si no hay puerto, o sea que es el ultimo switch del camino y no sabes donde esta conectado,
        # hardcodear el puerto del s7-->h7 ( te lo dice links de mininet )
        # if portt is None:
        #   msg = of.ofp_flow_mod()
        #   msg.data = event.ofp
        #   msg.match.dl_src = packet.src
        #   msg.match.dl_dst = packet.dst
        #   msg.actions.append(of.ofp_action_output(port=3))
        #   event.connection.send(msg)
        #
        # else:
        #   msg = of.ofp_flow_mod()
        #   msg.data = event.ofp
        #   msg.match.dl_src = packet.src
        #   msg.match.dl_dst = packet.dst
        #   msg.actions.append(of.ofp_action_output(port=portt))
        #   event.connection.send(msg)

        # Fin (1)

  def update(self, flow, next_sw):
    msg = of.ofp_flow_mod()
    msg.data = ''
    msg.match.nw_src = flow.src_ip
    msg.match.nw_dst = flow.dst_ip
    msg.match.tp_src = flow.src_port
    msg.match.tp_dst = flow.dst_port
    msg.match.nw_proto = flow.protocol
    msg.match.dl_type = 0x800
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
    msg.data = ''
    msg.match.nw_src = flow.src_ip
    msg.match.nw_dst = flow.dst_ip
    msg.match.tp_src = flow.src_port
    msg.match.tp_dst = flow.dst_port
    msg.match.nw_proto = flow.protocol
    msg.match.dl_type = 0x800
    print("forward", self.dpid)

    msg.actions.append(of.ofp_action_output(port=3))
    self.connection.send(msg)



