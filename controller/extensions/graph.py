class Graph:

    def __init__(self):
        self.dict = {}

    def add_node(self, node):
        if node not in self.dict:
            self.dict[node] = []
        self.print_graph()

    def add_edge(self, node1, node2):
        if node1 in self.dict:
            self.dict[node1].append(node2)
        else:
            self.dict[node1] = [node2]
        self.print_graph()

    def remove_edge(self, node1, node2):
        self.dict[node1].remove(node2)
        self.print_graph()

    def remove_node(self, node):
        if node in self.dict:
            del self.dict[node]
        self.print_graph()

    def print_graph(self):
        print(self.dict)
        print('\n')
