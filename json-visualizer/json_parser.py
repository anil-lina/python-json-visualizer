import networkx as nx

def json_to_graph(data):
    """
    Converts a JSON-like Python object to a networkx DiGraph.
    """
    G = nx.DiGraph()
    _add_node_recursive(G, data, parent_id=None, key=None)
    return G

def _add_node_recursive(G, data, parent_id, key):
    """
    Recursively adds nodes to the graph.
    """
    node_id = len(G)
    if isinstance(data, dict):
        G.add_node(node_id, type='object', label='{}')
        if parent_id is not None:
            G.add_edge(parent_id, node_id, label=key)
        for k, v in data.items():
            _add_node_recursive(G, v, node_id, k)
    elif isinstance(data, list):
        G.add_node(node_id, type='array', label='[]')
        if parent_id is not None:
            G.add_edge(parent_id, node_id, label=key)
        for i, item in enumerate(data):
            _add_node_recursive(G, item, node_id, str(i))
    else:
        node_type = 'string' if isinstance(data, str) else \
                    'number' if isinstance(data, (int, float)) else \
                    'boolean' if isinstance(data, bool) else \
                    'null' if data is None else 'unknown'
        label = f'"{data}"' if isinstance(data, str) else str(data)
        if data is None: label = 'null'
        if isinstance(data, bool): label = str(data)
        G.add_node(node_id, type=node_type, value=data, label=label)
        if parent_id is not None:
            G.add_edge(parent_id, node_id, label=key)

def graph_to_json(graph):
    """
    Converts a networkx DiGraph back to a JSON-like Python object.
    """
    if not graph:
        return None
    root = next((n for n, d in graph.in_degree() if d == 0), 0)
    if root is None:
        return None
    return _build_json_recursive(graph, root)

def _build_json_recursive(graph, node_id):
    """
    Recursively builds the JSON object from the graph.
    """
    node_data = graph.nodes[node_id]
    node_type = node_data.get('type')
    if node_type == 'object':
        return {graph.get_edge_data(node_id, s).get('label', ''): _build_json_recursive(graph, s) for s in graph.successors(node_id)}
    elif node_type == 'array':
        successors = sorted(graph.successors(node_id), key=lambda s: int(graph.get_edge_data(node_id, s).get('label', '0')))
        return [_build_json_recursive(graph, s) for s in successors]
    else:
        return node_data.get('value')
