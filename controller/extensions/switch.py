from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class SwitchController:
  def __init__(self, dpid, connection):
    self.dpid = dpid_to_str(dpid)
    self.connection = connection
    # El SwitchController se agrega como handler de los eventos del switch
    self.connection.addListeners(self)

    # "FW table", con pares (switch, MAC-addr)
    self.table = {}

  def _handle_PacketIn(self, event):
    """
    Esta funcion es llamada cada vez que el switch recibe un paquete
    y no encuentra en su tabla una regla para rutearlo
    """
    packet = event.parsed
    ip = packet.find('ipv4')
    if ip:
      log.info("%s, puerto %s : Ping %s -> %s", event.connection, event.port, ip.srcip, ip.dstip)

      #Actualizo la tabla
      self.table[(event.connection, packet.src)] = event.port

      dst_port = self.table.get((event.connection, packet.dst))

      # Si no hay puerto envia por todos los puertos menos por el cual llego
      if dst_port is None:
        msg = of.ofp_packet_out(data=event.ofp)
        msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL))
        event.connection.send(msg)

      # Si hay puerto envia por ese
      else:
        msg = of.ofp_flow_mod()
        msg.data = event.ofp
        msg.match.dl_src = packet.src
        msg.match.dl_dst = packet.dst
        msg.actions.append(of.ofp_action_output(port=dst_port))
        event.connection.send(msg)
