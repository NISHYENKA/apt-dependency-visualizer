"""External dpkg oracle; never used by the application for discovery."""

from itertools import product
import shutil
import subprocess
import unittest

from src.apt_graph.versions import compare_versions


@unittest.skipUnless(shutil.which('dpkg'), 'dpkg oracle requires Linux')
class DpkgTests(unittest.TestCase):
    """Compare tricky Debian versions against the native package utility."""

    def test_native_ordering(self):
        """Check every pair against dpkg --compare-versions."""
        versions = ['0', '1', '1-0', '0:1', '1~rc1', '1~~', '1.0',
                    '1.01', '1.1', '1.9', '1.10', '1+git', '1a',
                    '1-1ubuntu2', '1-1ubuntu10', '1:0', '2:0',
                    '1.0~beta2', '1.0~beta11', '1.0-0ubuntu1']
        relation = {-1: 'lt', 0: 'eq', 1: 'gt'}
        for left, right in product(versions, repeat=2):
            operator = relation[compare_versions(left, right)]
            result = subprocess.run(['dpkg', '--compare-versions', left,
                                     operator, right], check=False)
            self.assertEqual(result.returncode, 0, (left, right, operator))
