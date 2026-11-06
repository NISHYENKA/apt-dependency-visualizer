"""Validate the six command-line settings without network side effects."""

import argparse
from pathlib import Path
import re
from urllib.parse import urlsplit


default_repository = (
    'https://archive.ubuntu.com/ubuntu/dists/noble/main/'
    'binary-amd64/Packages.xz'
)
max_depth = 200
min_depth = 0


def depth_value(text):
    """Accept a bounded BFS level count, with the root at level zero."""
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError('depth must be an integer') from error
    if not min_depth <= value <= max_depth:
        raise argparse.ArgumentTypeError('depth must be between 0 and 200')
    return value


def validate_url(text):
    """Require an HTTP(S) index URL without credentials or fragments."""
    parts = urlsplit(text)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise ValueError('repository must be an HTTP(S) Packages index URL')
    if parts.username or parts.password or parts.fragment:
        raise ValueError('repository credentials and fragments are forbidden')
    if any(char.isspace() for char in text):
        raise ValueError('repository URL contains whitespace')
    _ = parts.port


def validate_settings(settings):
    """Check names, exact version and repository location for both modes."""
    pattern = r'[A-Z]' if settings.test_mode else r'[a-z0-9][a-z0-9+.-]+'
    if not re.fullmatch(pattern, settings.package):
        raise ValueError('invalid package name (test names must be A-Z)')
    if not re.fullmatch(r'(?:[0-9]+:)?[0-9][A-Za-z0-9.+:~\-]*',
                        settings.version):
        raise ValueError('version must be an explicit Debian package version')
    if settings.test_mode:
        path = Path(settings.repository)
        if not path.is_file():
            raise ValueError('test repository file does not exist')
        with path.open('rb') as stream:
            stream.read(1)
    else:
        validate_url(settings.repository)


def parse_args(argv=None):
    """Return validated CLI options or terminate with argparse error code 2."""
    parser = argparse.ArgumentParser(description='Ubuntu dependency graph')
    parser.add_argument('--package', required=True)
    parser.add_argument('--repository', default=default_repository)
    parser.add_argument('--test-mode', action='store_true')
    parser.add_argument('--version', required=True)
    parser.add_argument('--ascii', action='store_true')
    parser.add_argument('--max-depth', type=depth_value, default=5)
    settings = parser.parse_args(argv)
    try:
        validate_settings(settings)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    return settings
