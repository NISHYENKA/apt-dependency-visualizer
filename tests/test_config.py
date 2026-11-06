"""CLI validation and prototype output tests."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from src.apt_graph.config import parse_args


class ConfigTests(unittest.TestCase):
    """Each configurable parameter has both valid and invalid cases."""

    def test_defaults(self):
        """Required arguments preserve exact package version."""
        settings = parse_args(['--package', 'bash', '--version', '5.2-1'])
        self.assertEqual(settings.version, '5.2-1')
        self.assertEqual(settings.max_depth, 5)
        self.assertFalse(settings.ascii)

    def test_bad_arguments(self):
        """Reject invalid values, flag values and missing required options."""
        base = ['--package', 'bash', '--version', '5.2-1']
        cases = [[], ['--package', 'bash'],
                 base + ['--package', '../bash'],
                 base + ['--version', 'latest'],
                 base + ['--repository', 'ftp://example.com'],
                 base + ['--repository', 'https://user@host/index'],
                 base + ['--repository', 'https://host:bad/index'],
                 base + ['--test-mode', 'false'],
                 base + ['--ascii', 'false'],
                 base + ['--max-depth', '-1'],
                 base + ['--max-depth', '201'],
                 base + ['--max-depth', 'text']]
        for args in cases:
            with self.subTest(args=args), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    parse_args(args)
                self.assertEqual(caught.exception.code, 2)

    def test_test_repository(self):
        """Accept readable local files and uppercase test package names."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'graph.json'
            path.write_text('{}', encoding='utf-8')
            args = ['--package', 'A', '--version', '1', '--test-mode',
                    '--repository', str(path), '--ascii', '--max-depth', '0']
            settings = parse_args(args)
            self.assertTrue(settings.ascii)
            self.assertEqual(settings.max_depth, 0)
            path.unlink()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                parse_args(args)

    def test_help(self):
        """Help exits successfully without mandatory arguments."""
        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as cm:
            parse_args(['--help'])
        self.assertEqual(cm.exception.code, 0)
