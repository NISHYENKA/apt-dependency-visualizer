"""Common methodology checks, available from the first stage."""

import ast
from pathlib import Path
import unittest


root = Path(__file__).resolve().parents[1]


class StructureTests(unittest.TestCase):
    """Check required paths and reviewability limits."""

    def test_required_files(self):
        """Every stage has documentation, source, tests and a launcher."""
        for name in ('README.md', '.gitignore', 'src', 'tests', 'run.bat'):
            self.assertTrue((root / name).exists(), name)

    def test_python_limits(self):
        """Inspect size, arguments, docstrings and comparison literals."""
        for folder in ('src', 'tests'):
            for path in (root / folder).rglob('*.py'):
                source = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(source.splitlines()), 1000, str(path))
                for line in source.splitlines():
                    self.assertLessEqual(len(line), 80, f'{path}: {line}')
                for node in ast.walk(ast.parse(source)):
                    self.check_node(node, path)

    def check_node(self, node, path):
        """Validate the syntax nodes relevant to the methodology."""
        if isinstance(node, ast.FunctionDef):
            self.assertLessEqual(node.end_lineno - node.lineno + 1, 40,
                                 f'{path}: {node.name}')
            self.assertLessEqual(len(node.args.args), 7)
            self.assertTrue(ast.get_docstring(node), node.name)
        if isinstance(node, ast.Compare):
            for item in [node.left] + node.comparators:
                if isinstance(item, ast.Constant):
                    self.assertNotIn(type(item.value), (int, float))
