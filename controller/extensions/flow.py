class Flow:
    def __init__(self, src_ip, src_port, dst_ip, dst_port, protocol):
        self.dst_port = dst_port
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.src_ip = src_ip
        self.protocol = protocol
