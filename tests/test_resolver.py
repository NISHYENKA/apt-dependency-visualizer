"""Resolve declared version constraints, alternatives and virtual packages."""

import unittest

from src.apt_graph.resolver import ResolvedRepository


class ResolverTests(unittest.TestCase):
    """Version selection must not silently replace constraints with latest."""

    def test_constraints_and_alternatives(self):
        """Select highest matching version and every available alternative."""
        text = ('Package: root\nVersion: 1\n'
                'Depends: aa (<< 2), missing | bb\n\n'
                'Package: aa\nVersion: 1.9\n\n'
                'Package: aa\nVersion: 1.10\n\n'
                'Package: aa\nVersion: 2\n\n'
                'Package: bb\nVersion: 1\n')
        repo = ResolvedRepository(text)
        self.assertEqual(repo.children('root@1'), ['aa@1.10', 'bb@1'])

    def test_versioned_provider(self):
        """Test the Provides version, not the provider package version."""
        text = ('Package: root\nVersion: 1\nDepends: virtual (>= 2)\n\n'
                'Package: provider\nVersion: 9\nProvides: virtual (= 2)\n\n'
                'Package: legacy\nVersion: 99\nProvides: virtual\n')
        repo = ResolvedRepository(text)
        self.assertEqual(repo.children('root@1'), ['provider@9'])

    def test_unresolved(self):
        """A missing required dependency is an explicit error."""
        repo = ResolvedRepository('Package: root\nVersion: 1\nDepends: lost')
        with self.assertRaisesRegex(ValueError, 'lost'):
            repo.children('root@1')

    def test_architecture(self):
        """Foreign architecture requirements cannot match an amd64 record."""
        repo = ResolvedRepository('Package: libc6\nVersion: 1\n'
                                  'Architecture: amd64\n')
        self.assertEqual(repo.targets(('libc6', 'arm64', None, None)), [])
        self.assertEqual(repo.targets(('libc6', 'any', None, None)),
                         ['libc6@1'])
