"""Read Debian binary control stanzas from an Ubuntu Packages index."""

import re


def parse_stanzas(text):
    """Unfold continuation lines and reject malformed or duplicate fields."""
    stanza = {}
    key = None
    for line in text.splitlines() + ['']:
        if not line.strip():
            if stanza:
                yield stanza
            stanza, key = {}, None
        elif line.startswith((' ', '\t')):
            if key is None:
                raise ValueError('orphan continuation in Packages index')
            stanza[key] += ' ' + line.strip()
        else:
            name, separator, value = line.partition(':')
            key = name.lower()
            if not separator or not re.fullmatch(r'[A-Za-z][\w-]*', name):
                raise ValueError('malformed field in Packages index')
            if key in stanza:
                raise ValueError(f'duplicate control field: {name}')
            stanza[key] = value.strip()


def parse_packages(text):
    """Index binary package records by name and exact version."""
    packages = {}
    for record in parse_stanzas(text):
        name = record.get('package', '')
        version = record.get('version', '')
        if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name) or not version:
            raise ValueError('Packages record lacks valid Package/Version')
        key = f'{name}@{version}'
        if key in packages:
            raise ValueError(f'duplicate package version: {key}')
        packages[key] = record
    if not packages:
        raise ValueError('empty Packages index')
    return packages


def declarations(record):
    """Return mandatory Pre-Depends and Depends as intact OR groups."""
    text = ','.join(record.get(field, '')
                    for field in ('pre-depends', 'depends'))
    return [group.strip() for group in text.split(',') if group.strip()]
