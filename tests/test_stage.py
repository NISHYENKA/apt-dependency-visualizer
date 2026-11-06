"""Checks specific to the current stage output."""

from contextlib import redirect_stdout
from io import StringIO
import unittest

from src.apt_graph.main import main


class StageTests(unittest.TestCase):
    """The prototype reports every setting without querying a repository."""

    def test_configuration_output(self):
        """Exactly six key-value lines are printed."""
        output = StringIO()
        with redirect_stdout(output):
            result = main(['--package', 'bash', '--version', '5.2-1'])
        self.assertEqual(result, 0)
        self.assertEqual(len(output.getvalue().splitlines()), 6)
        self.assertIn('version=5.2-1', output.getvalue())
