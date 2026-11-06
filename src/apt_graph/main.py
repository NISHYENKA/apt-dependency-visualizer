"""Stage 2: display direct dependencies of an exact Ubuntu package version."""

from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'src.apt_graph'

from .config import parse_args
from .repository import AptRepository, download_index


def main(argv=None):
    """Fetch direct dependency declarations or report a readable error."""
    settings = parse_args(argv)
    try:
        if settings.test_mode:
            raise ValueError('test repository support starts at stage 3')
        repository = AptRepository(download_index(settings.repository))
        root = repository.root(settings.package, settings.version)
        for group in repository.direct(root):
            print(group)
    except (OSError, ValueError, EOFError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
