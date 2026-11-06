"""Stage 5: render the forward graph with PlantUML and optional ASCII."""

from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'src.apt_graph'

from .config import parse_args
from .fixtures import TestRepository
from .graph import build_graph
from .render import ascii_tree, save_diagram
from .repository import download_index
from .resolver import ResolvedRepository


def load_repository(settings):
    """Select a validated local fixture or a downloaded Ubuntu index."""
    if settings.test_mode:
        return TestRepository(settings.repository)
    return ResolvedRepository(download_index(settings.repository))


def main(argv=None):
    """Render the diagram and optional tree, suppressing earlier outputs."""
    settings = parse_args(argv)
    try:
        repository = load_repository(settings)
        root = repository.root(settings.package, settings.version)
        graph = build_graph(root, repository.children, settings.max_depth)
        destination = save_diagram(graph, settings.package)
        print(f'Image: {destination}')
        if settings.ascii:
            print(ascii_tree(graph, root))
    except (OSError, ValueError, EOFError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
