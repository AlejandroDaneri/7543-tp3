from pox.core import core

log = core.getLogger()


class Graph:

    def __init__(self):
        # Como clave tiene la MAC de un switch y como valor
        # un array de sw que tiene directamente conectados
        self.dict = {}

    def add_node(self, node):
        if node not in self.dict:
            self.dict[node] = []
            self.print_graph()

    def add_edge(self, src_node, dst_node):
        if src_node in self.dict:
            self.dict[src_node].append(dst_node)
        else:
            self.dict[src_node] = [dst_node]
        self.print_graph()

    def remove_edge(self, src_node, dst_node):
        self.dict[src_node].remove(dst_node)
        self.print_graph()

    def remove_node(self, node):
        if node in self.dict:
            del self.dict[node]
            self.print_graph()

    def print_graph(self):
        log.debug(self.dict)

    def nodes(self):
        return self.dict.keys()

    def neighbours(self, node):
        return self.dict[node]
