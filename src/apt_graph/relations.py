"""Parse binary dependency alternatives and versioned virtual Provides."""

import re

from .versions import split_version


atom_pattern = re.compile(
    r'([a-z0-9][a-z0-9+.-]+)(?::([a-z0-9-]+))?'
    r'(?:\s*\(\s*(<<|<=|=|>=|>>)\s*([^\s()]+)\s*\))?'
)


def parse_atom(text):
    """Return name, architecture qualifier, operator and required version."""
    match = atom_pattern.fullmatch(text.strip())
    if not match:
        raise ValueError(f'unsupported binary dependency: {text}')
    name, architecture, operator, version = match.groups()
    if version:
        split_version(version)
    return name, architecture, operator, version


def parse_group(text):
    """Preserve every OR alternative in its original declaration order."""
    return [parse_atom(item) for item in text.split('|')]


def provided_names(record):
    """Read unversioned or exact-version Provides, rejecting other operators."""
    result = []
    for item in record.get('provides', '').split(','):
        if not item.strip():
            continue
        name, architecture, operator, version = parse_atom(item)
        if architecture or operator not in (None, '='):
            raise ValueError(f'invalid Provides: {item}')
        result.append((name, version))
    return result
