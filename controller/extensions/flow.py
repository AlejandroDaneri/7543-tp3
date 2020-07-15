class Flow:
    # TODO: separar ip/port en clases aparte (Host tal vez?)
    # NOTA: le puse el packet para poder obtener la MAC src/dst
    def __init__(self, src_ip, src_port, dst_ip, dst_port, protocol, packet):
        self.dst_port = dst_port
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.src_ip = src_ip
        self.protocol = protocol

        self.packet = packet
