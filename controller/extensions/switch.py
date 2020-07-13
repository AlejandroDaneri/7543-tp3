from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
from extensions.dijkstra import shortest_path


log = core.getLogger()

class SwitchController:
  def __init__(self, dpid, connection, graph, hosts):
    self.dpid = dpid_to_str(dpid)
    self.connection = connection
    # El SwitchController se agrega como handler de los eventos del switch
    self.connection.addListeners(self)

    # "CAM table", con pares (MAC-addr, port)
    # TODO: cosas a guardar para matchear dst_port, src_port, dst_ip, src_ip, protocol
    self.table = {}

    self.graph = graph

    self.hosts = hosts

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



      # # Descarta el paquete si el puerto de salida es igual al de entrada
      # if dst_port == event.port:
      #   return
      #
      # # Si no hay puerto envia por todos los puertos menos por el cual llego (flooding)
      # if dst_port is None:
      #   msg = of.ofp_packet_out(data=event.ofp)
      #   msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL))
      #   event.connection.send(msg)
      #
      # # Si hay puerto envia por ese
      # else:
      # msg = of.ofp_flow_mod()
      # msg.data = event.ofp
      # msg.match.dl_src = packet.src
      # msg.match.dl_dst = packet.dst
      # msg.actions.append(of.ofp_action_output(port=dst_port))
      # event.connection.send(msg)


      # Hardcodeo de prueba, para saber magicamente el switch de h7 cuando hago X--ping->h7 en topo de 3 lvls
      if (ip.dstip == '10.0.0.7') or (ip.srcip in self.hosts):
        dest = '00-00-00-00-00-07'

        if ip.dstip != '10.0.0.7':
          dest = self.hosts[ip.dstip]
        print(shortest_path(self.graph, self.hosts[ip.srcip], dest))

        path = shortest_path(self.graph, self.hosts[ip.srcip], dest)
        next_sw = path.popleft()

        portt = self.graph.get_port_to(dpid_to_str(event.dpid), next_sw)
        print(next_sw)
        print(portt)

        # (1) Lo que sigue deberia mandarse para guardar en todos los switches del path
        # porque de esta forma no funciona
        # EJ: path (00-01,00-02, 00-07) y suponiendo que de s1 a s2 voy por puerto 3 y de s2 a s7,puerto 5
        # entonces, decirle al s1 que el paquete con tal ip_src y tal ip_dest vaya puerto 3
        # s2 con ese mismo ip_src y ip_dest vaya por puerto 5 ,etc

        # Si no hay puerto, o sea que es el ultimo switch del camino y no sabes donde esta conectado,
        # hardcodear el puerto del s7-->h7 ( te lo dice links de mininet )
        if portt is None:
          msg = of.ofp_flow_mod()
          msg.data = event.ofp
          msg.match.dl_src = packet.src
          msg.match.dl_dst = packet.dst
          msg.actions.append(of.ofp_action_output(port=3))
          event.connection.send(msg)

        else:
          msg = of.ofp_flow_mod()
          msg.data = event.ofp
          msg.match.dl_src = packet.src
          msg.match.dl_dst = packet.dst
          msg.actions.append(of.ofp_action_output(port=portt))
          event.connection.send(msg)

        # Fin (1)
