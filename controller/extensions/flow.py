from struct import pack
from zlib import crc32

class Flow:
    # TODO: separar ip/port en clases aparte (Host tal vez?)
    # NOTA: le puse el packet para poder obtener la MAC src/dst
    def __init__(self, src_ip, src_port, dst_ip, dst_port, protocol, src_hw, dst_hw):
        self.dst_port = dst_port
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.src_ip = src_ip
        self.protocol = protocol
        self.src_hw = src_hw
        self.dst_hw = dst_hw

    def flow_id(self):
        "Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0."
        hash_input = [0] * 5
        hash_input[0] = self.src_ip.toUnsigned()
        hash_input[1] = self.dst_ip.toUnsigned()
        hash_input[2] = self.protocol
        hash_input[3] = self.src_port
        hash_input[4] = self.dst_port
        return crc32(pack('LLHHH', *hash_input))
