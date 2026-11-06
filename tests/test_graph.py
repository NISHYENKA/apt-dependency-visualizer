"""BFS depth, ordering, shared subgraphs, cycles and local input errors."""

import json
from pathlib import Path
import tempfile
import unittest

from src.apt_graph.fixtures import TestRepository, validate_graph
from src.apt_graph.graph import build_graph


class GraphTests(unittest.TestCase):
    """Distinguish true breadth-first discovery from depth-first traversal."""

    def test_breadth_first(self):
        """A shared child reached directly retains its full depth budget."""
        data = {'A': ['B', 'D'], 'B': ['C'], 'C': ['D'],
                'D': ['E'], 'E': []}
        calls = []

        def children(node):
            """Record expansion order for a graph with unequal path lengths."""
            calls.append(node)
            return data[node]

        graph = build_graph('A', children, 2)
        self.assertEqual(calls, ['A', 'B', 'D'])
        self.assertEqual(list(graph), ['A', 'B', 'D', 'C', 'E'])
        self.assertEqual(graph['C'], [])

    def test_cycles(self):
        """Retain cycle edges while expanding every vertex only once."""
        data = {'A': ['B'], 'B': ['A', 'B']}
        self.assertEqual(build_graph('A', data.__getitem__, 200), data)

    def test_zero_depth(self):
        """Do not request children of a zero-depth root."""
        self.assertEqual(build_graph('A', None, 0), {'A': []})

    def test_chain_limit(self):
        """Include boundary vertices without traversing beyond the limit."""
        data = {'A': ['B'], 'B': ['C'], 'C': []}
        self.assertEqual(build_graph('A', data.__getitem__, 1),
                         {'A': ['B'], 'B': []})

    def test_invalid_fixture(self):
        """Reject malformed, lowercase and dangling graph definitions."""
        for data in ([], {}, {'a': []}, {'A': 'B'}, {'A': ['B']},
                     {'A': [3]}, {'A': [{}]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_graph(data)

    def test_fixture_version(self):
        """Version is still required for synthetic repositories."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.json'
            path.write_text(json.dumps({'A': ['A', 'A']}), encoding='utf-8')
            repo = TestRepository(path)
            self.assertEqual(repo.root('A', '1'), 'A')
            self.assertEqual(repo.children('A'), ['A'])
            for name, version in [('A', '2'), ('B', '1')]:
                with self.assertRaises(ValueError):
                    repo.root(name, version)
