"""Output and error handling for graph construction."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from src.apt_graph.main import main


class StageTests(unittest.TestCase):
    """Stage 3 prints resolved graph edges without configuration output."""

    def test_direct_output(self):
        """Use the requested version even if a newer record is present."""
        data = ('Package: bash\nVersion: 1\nDepends: libc6 (>= 2)\n\n'
                'Package: libc6\nVersion: 2\n\n'
                'Package: bash\nVersion: 2\nDepends: other\n')
        output = StringIO()
        with patch('src.apt_graph.main.download_index', return_value=data):
            with redirect_stdout(output):
                result = main(['--package', 'bash', '--version', '1'])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(),
                         'bash@1 -> libc6@2\nlibc6@2 -> (none)\n')

    def test_network_error(self):
        """Network failures produce a nonzero result, not a traceback."""
        with patch('src.apt_graph.main.download_index', side_effect=OSError):
            with redirect_stderr(StringIO()):
                self.assertEqual(main(['--package', 'bash',
                                       '--version', '1']), 1)
