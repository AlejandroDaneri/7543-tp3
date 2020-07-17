from collections import deque

def shortest_path(graph, src, dst):
    # 1. Mark all nodes unvisited and store them.
    # 2. Set the distance to zero for our initial node
    # and to infinity for other nodes.
    distances = {vertex: float('inf') for vertex in graph.nodes()}
    previous_vertices = {
        vertex: None for vertex in graph.nodes()
    }
    distances[src] = 0
    vertices = graph.nodes()

    while vertices:
        # 3. Select the unvisited node with the smallest distance,
        # it's current node now.
        current_vertex = min(
            vertices, key=lambda vertex: distances[vertex])

        # 6. Stop, if the smallest distance
        # among the unvisited nodes is infinity.
        if distances[current_vertex] == float('inf'):
            break

        # 4. Find unvisited neighbors for the current node
        # and calculate their distances through the current node.
        for neighbour in graph.neighbours(current_vertex):
            alternative_route = distances[current_vertex]

            # Compare the newly calculated distance to the assigned
            # and save the smaller one.
            if alternative_route < distances[neighbour]:
                distances[neighbour] = alternative_route  # +1 (costo)?
                previous_vertices[neighbour] = current_vertex

        # 5. Mark the current node as visited
        # and remove it from the unvisited set.
        vertices.remove(current_vertex)

    path, current_vertex = deque(), dst
    while previous_vertices[current_vertex] is not None:
        path.appendleft(current_vertex)
        current_vertex = previous_vertices[current_vertex]
    if path:
        path.appendleft(current_vertex)
    return path

def _find_all_paths(graph, src, dst, path=[]):
    path = path + [src]
    if src == dst:
        return [path]
    if src not in graph.nodes():
        return []
    paths = []
    for vertex in graph.neighbours(src):
        if vertex not in path:
            extended_paths = _find_all_paths(graph, vertex, dst, path)
            for p in extended_paths: 
                paths.append(p)
    return paths

def find_all_paths(graph, src, dst):
    """Encuentra todos los paths y elije los de menor tamanio"""
    paths = _find_all_paths(graph, src, dst)
    minimum_length = min([len(path) for path in paths])
    return deque([path for path in paths if len(path) == minimum_length])