from mininet.topo import Topo
from itertools import product

CLIENTS = 3

class FatTree(Topo):

    def __init__(self, levels=3, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)
        if levels < 1:
            return
        self.create_levels(levels, CLIENTS)

    def create_levels(self, levels, clients_num):
        # Agrego los 3 hosts "iniciales", cada uno con nombre h_{1, 2...}
        # Empiezo desde el 1 ya que mininet linkea por defecto h1 con ip 00...01 ,etc
        clients = [self.addHost('h{}'.format(i+1)) for i in range(clients_num)]
        prev_sw = []
        switches = []

        for level in range(levels):
            # Por cada uno de los niveles, agrego 2^nivel switches
            switches_count = 2**level

            # Empiezo desde el 1 ya que mininet linkea por defecto mac de s1 con 00-00-..-01 ,etc
            # nivel = floor(log2(#swith)), siendo nivel=0 el primer nivel
            switches = [self.addSwitch('s{}'.format(2**(level+1)-(switches_count-n))) for n in range(switches_count)]

            if prev_sw:
                # Estoy en un nivel no-root, agrego links entre todos los
                # switches del nivel anterior y este
                for a, b in product(prev_sw, switches):
                    self.addLink(a, b)
            else:
                # Estoy en el root
                assert len(switches) == 1  # Redundante, pero por las dudas
                # Agrego un link entre los clientes (hosts iniciales) y mi
                # switch root
                for client in clients:
                    self.addLink(client, switches[0])

            # Continuo el ciclo
            prev_sw = switches

        # Creo un proveedor por cada switch hoja y agrego un link entre el host
        # y el switch
        host_num = clients_num
        for sw in switches:
            leaf = self.addHost('h{}'.format(host_num+1))
            self.addLink(sw, leaf)
            host_num += 1

topos = { 'fat_tree': FatTree  }
