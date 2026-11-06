"""Stage 1: display all user-configurable parameters."""

from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'src.apt_graph'

from .config import parse_args


def main(argv=None):
    """Validate settings and display the six key-value pairs."""
    settings = parse_args(argv)
    for key, value in vars(settings).items():
        print(f'{key}={value}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
