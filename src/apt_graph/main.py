"""Stage 4: show reverse dependencies using the same recursive BFS."""

from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'src.apt_graph'

from .config import parse_args
from .fixtures import TestRepository
from .graph import build_graph, graph_lines
from .repository import download_index
from .resolver import ResolvedRepository
from .reverse import reverse_index


def load_repository(settings):
    """Select a validated local fixture or a downloaded Ubuntu index."""
    if settings.test_mode:
        return TestRepository(settings.repository)
    return ResolvedRepository(download_index(settings.repository))


def main(argv=None):
    """Print reverse BFS edges across the entire selected repository."""
    settings = parse_args(argv)
    try:
        repository = load_repository(settings)
        root = repository.root(settings.package, settings.version)
        reverse = reverse_index(repository)
        graph = build_graph(root, reverse.__getitem__, settings.max_depth)
        print('\n'.join(graph_lines(graph)))
    except (OSError, ValueError, EOFError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
