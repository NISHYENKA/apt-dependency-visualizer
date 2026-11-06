"""PlantUML output, truthful ASCII markers and safe renderer failures."""

from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.apt_graph.render import ascii_tree, render_svg, save_diagram
from src.apt_graph.render import to_plantuml


class RenderTests(unittest.TestCase):
    """Check data fidelity and preserve existing diagrams on renderer error."""

    def test_plantuml(self):
        """Every graph edge appears exactly once, including cycle edges."""
        graph = {'aa@1': ['bb@2'], 'bb@2': ['aa@1']}
        source = to_plantuml(graph)
        self.assertIn('rectangle "aa@1" as n0', source)
        self.assertIn('n1 --> n0', source)
        self.assertEqual(source.count(' --> '), 2)
        self.assertTrue(source.endswith('@enduml\n'))

    def test_ascii(self):
        """Shared nodes are not incorrectly described as cycles."""
        graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': ['A']}
        tree = ascii_tree(graph, 'A')
        self.assertIn('A [cycle]', tree)
        self.assertIn('D [shared]', tree)
        self.assertEqual(tree.splitlines()[0], 'A')

    def test_missing_renderer(self):
        """An actionable error is raised when Java is missing."""
        with patch('src.apt_graph.render.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'Java'):
                render_svg('@startuml\n@enduml')

    def test_invalid_renderer_output(self):
        """Reject failure status, non-SVG content and timeout."""
        results = [SimpleNamespace(stdout=b'bad', stderr=b'', returncode=0),
                   SimpleNamespace(stdout=b'<html/>', stderr=b'', returncode=0)]
        with patch('src.apt_graph.render.shutil.which', return_value='java'), \
                patch('pathlib.Path.is_file', return_value=True):
            for result in results:
                with patch('src.apt_graph.render.subprocess.run',
                           return_value=result), self.assertRaises(ValueError):
                    render_svg('text')
            with patch('src.apt_graph.render.subprocess.run',
                       side_effect=subprocess.TimeoutExpired('java', 120)):
                with self.assertRaises(ValueError):
                    render_svg('text')

    def test_preserve_existing(self):
        """Failed rendering cannot overwrite a previously working diagram."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'generated'
            path.mkdir()
            image = path / 'A.svg'
            image.write_text('previous', encoding='utf-8')
            with patch('src.apt_graph.render.project_root', Path(folder)), \
                    patch('src.apt_graph.render.render_svg',
                          side_effect=ValueError('broken')):
                with self.assertRaises(ValueError):
                    save_diagram({'A': []}, 'A')
            self.assertEqual(image.read_text(encoding='utf-8'), 'previous')

    def test_save_and_open(self):
        """Publish both files and open the real file URI in the browser."""
        with tempfile.TemporaryDirectory() as folder:
            with patch('src.apt_graph.render.project_root', Path(folder)), \
                    patch('src.apt_graph.render.render_svg',
                          return_value=b'<svg/>'), \
                    patch('src.apt_graph.render.webbrowser.open') as browser:
                path = save_diagram({'A': []}, 'A')
            self.assertEqual(path.read_bytes(), b'<svg/>')
            self.assertIn('@startuml', path.with_suffix('.puml').read_text())
            browser.assert_called_once_with(path.as_uri())
