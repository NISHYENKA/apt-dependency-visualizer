"""Packages format, compressed downloads and exact version selection."""

import gzip
from io import BytesIO
import lzma
import unittest
from unittest.mock import patch

from src.apt_graph.control import declarations, parse_packages
from src.apt_graph.repository import AptRepository, download_index, unpack_index


sample = ('Package: bash\nVersion: 1\nPre-Depends: libc6 (>= 2)\n'
          'Depends: aa | bb,\n cc\n\nPackage: bash\nVersion: 2\n')


class RepositoryTests(unittest.TestCase):
    """Validate real control-format semantics without third-party parsers."""

    def test_exact_version(self):
        """Two versions remain separate and missing versions are errors."""
        repo = AptRepository(sample)
        self.assertEqual(repo.root('bash', '1'), 'bash@1')
        self.assertEqual(repo.direct('bash@1'),
                         ['libc6 (>= 2)', 'aa | bb', 'cc'])
        with self.assertRaisesRegex(ValueError, 'available'):
            repo.root('bash', '3')

    def test_invalid_control(self):
        """Reject corrupt fields and records instead of inventing leaves."""
        for text in ('', 'bad', ' continuation', 'Package: bash\n',
                     'Package: bash\nPackage: grep\nVersion: 1',
                     sample + '\nPackage: bash\nVersion: 2'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_packages(text)

    def test_compression(self):
        """Plain, gzip and xz content decode to the same index."""
        data = sample.encode()
        for packed in (data, gzip.compress(data), lzma.compress(data)):
            self.assertEqual(unpack_index(packed), sample)

    def test_download(self):
        """The HTTP reader unpacks the response body."""
        with patch('src.apt_graph.repository.urlopen',
                   return_value=BytesIO(gzip.compress(sample.encode()))):
            self.assertEqual(download_index('https://host/Packages.gz'),
                             sample)

    def test_limits(self):
        """Reject oversized compressed and expanded content."""
        with patch('src.apt_graph.repository.expanded_limit', 3):
            with self.assertRaises(ValueError):
                unpack_index(gzip.compress(sample.encode()))
        with patch('src.apt_graph.repository.download_limit', 3):
            with patch('src.apt_graph.repository.urlopen',
                       return_value=BytesIO(sample.encode())):
                with self.assertRaises(ValueError):
                    download_index('https://host/Packages')

    def test_no_dependencies(self):
        """A valid package without mandatory relationships is a leaf."""
        self.assertEqual(declarations({'package': 'leaf'}), [])

    def test_corrupt_compression(self):
        """Corrupt gzip/xz data becomes a readable application error."""
        for data in (b'\xfd7zXZ\x00broken', b'\x1f\x8bbroken'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                unpack_index(data)
