"""Reverse dependency tests including exact versions and unrelated roots."""

from types import SimpleNamespace
import unittest

from src.apt_graph.graph import build_graph
from src.apt_graph.resolver import ResolvedRepository
from src.apt_graph.reverse import reverse_index


class ReverseTests(unittest.TestCase):
    """Search the full repository, not just the root's forward closure."""

    def test_exact_older_version(self):
        """Reverse matches include an old version satisfying a declaration."""
        text = ('Package: target\nVersion: 1\n\n'
                'Package: target\nVersion: 2\n\n'
                'Package: older\nVersion: 1\nDepends: target (<= 1)\n\n'
                'Package: newer\nVersion: 1\nDepends: target (>= 2)\n\n'
                'Package: either\nVersion: 1\nDepends: target\n')
        reverse = reverse_index(ResolvedRepository(text))
        self.assertEqual(reverse['target@1'], ['older@1', 'either@1'])
        self.assertEqual(reverse['target@2'], ['newer@1', 'either@1'])

    def test_reverse_chain(self):
        """A leaf's reverse closure includes its otherwise invisible parents."""
        repo = SimpleNamespace(graph={'A': ['B'], 'B': ['C'], 'C': []})
        reverse = reverse_index(repo)
        self.assertEqual(build_graph('C', reverse.__getitem__, 2),
                         {'C': ['B'], 'B': ['A'], 'A': []})

    def test_cycle_and_depth(self):
        """The reused BFS retains reverse cycles and observes its boundary."""
        repo = SimpleNamespace(graph={'A': ['B'], 'B': ['C'], 'C': ['A']})
        reverse = reverse_index(repo)
        self.assertEqual(build_graph('A', reverse.__getitem__, 1),
                         {'A': ['C'], 'C': []})
        self.assertEqual(build_graph('A', reverse.__getitem__, 200), reverse)

    def test_versioned_provider(self):
        """Find dependents through versioned virtual Provides."""
        text = ('Package: root\nVersion: 1\nDepends: virtual (>= 2)\n\n'
                'Package: provider\nVersion: 9\nProvides: virtual (= 2)\n')
        self.assertEqual(reverse_index(ResolvedRepository(text))['provider@9'],
                         ['root@1'])

    def test_empty(self):
        """An isolated root has no reverse dependencies."""
        self.assertEqual(reverse_index(SimpleNamespace(graph={'A': []})),
                         {'A': []})
