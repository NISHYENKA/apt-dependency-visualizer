"""Read a small A-Z test repository without contacting the network."""

import json
from pathlib import Path
import re


def validate_graph(graph):
    """Require declared uppercase vertices and lists of valid references."""
    if not isinstance(graph, dict) or not graph:
        raise ValueError('test repository must be a nonempty object')
    for key, children in graph.items():
        if not re.fullmatch(r'[A-Z]', key) or not isinstance(children, list):
            raise ValueError('test nodes must be A-Z with list values')
        for child in children:
            if not isinstance(child, str) or child not in graph:
                raise ValueError(f'undeclared test dependency: {child}')


class TestRepository:
    """Give each test vertex the fixed version 1."""

    def __init__(self, path):
        """Read JSON and validate every edge before traversal."""
        self.graph = json.loads(Path(path).read_text(encoding='utf-8'))
        validate_graph(self.graph)

    def root(self, name, version):
        """Reject absent names and versions even with zero traversal depth."""
        if name not in self.graph or version != '1':
            raise ValueError('test package not found; test version is 1')
        return name

    def children(self, key):
        """Return deduplicated edges in stable declaration order."""
        return list(dict.fromkeys(self.graph[key]))
