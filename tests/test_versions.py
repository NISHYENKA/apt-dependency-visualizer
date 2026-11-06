"""Debian version ordering and binary dependency relationships."""

import unittest

from src.apt_graph.relations import parse_atom, parse_group, provided_names
from src.apt_graph.versions import compare_versions, satisfies


class VersionTests(unittest.TestCase):
    """Exercise epochs, revision defaults, tilde and numerical ordering."""

    def test_order(self):
        """Debian order differs from both lexical order and SemVer."""
        pairs = [('1~rc1', '1'), ('1~~', '1~'), ('1', '1+git'),
                 ('1a', '1+'), ('1.9', '1.10'), ('9:99', '10:1'),
                 ('1-1', '1-2'), ('1-1ubuntu2', '1-1ubuntu10'),
                 ('1.0~beta2', '1.0~beta11')]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertEqual(compare_versions(left, right), -1)
                self.assertEqual(compare_versions(right, left), 1)

    def test_equal_versions(self):
        """Missing revision and epoch default to zero."""
        for left, right in [('1', '1-0'), ('0:1', '1'), ('1.01', '1.1')]:
            self.assertEqual(compare_versions(left, right), 0)

    def test_operators(self):
        """All five operators respect their inclusive or strict boundaries."""
        for operator in ('=', '<=', '>='):
            self.assertTrue(satisfies('1', operator, '1'))
        for operator in ('<<', '>>'):
            self.assertFalse(satisfies('1', operator, '1'))
        self.assertTrue(satisfies('2', '>>', '1'))
        self.assertTrue(satisfies('1', '<<', '2'))

    def test_relationships(self):
        """Parse qualifiers, alternatives and versioned Provides."""
        self.assertEqual(parse_atom('libc6:any (>= 2.38)'),
                         ('libc6', 'any', '>=', '2.38'))
        self.assertEqual(len(parse_group('aa | bb (<< 2)')), 2)
        self.assertEqual(provided_names({'provides': 'virtual (= 3), other'}),
                         [('virtual', '3'), ('other', None)])
        for text in ('bad!', 'aa (> 1)', 'aa [amd64]', 'aa (>= latest)'):
            with self.assertRaises(ValueError):
                parse_atom(text)

    def test_invalid_versions(self):
        """Reject non-Debian version strings."""
        for text in ('latest', '', '1 2', 'x:1'):
            with self.assertRaises(ValueError):
                compare_versions(text, '1')
