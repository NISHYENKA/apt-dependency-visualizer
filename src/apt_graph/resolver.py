"""Resolve Ubuntu declarations inside one downloaded binary index."""

from functools import cmp_to_key

from .relations import parse_group, provided_names
from .repository import AptRepository
from .versions import compare_versions, satisfies, split_version


class ResolvedRepository(AptRepository):
    """Keep versioned nodes and explicit alternative/provider edges."""

    def __init__(self, text):
        """Index real names and virtual providers once per repository."""
        super().__init__(text)
        self.names = {}
        self.providers = {}
        for key, record in self.records.items():
            split_version(record['version'])
            self.names.setdefault(record['package'], []).append(key)
            for name, version in provided_names(record):
                self.providers.setdefault(name, []).append((key, version))

    def architecture_matches(self, key, qualifier):
        """Accept native/any within the single-architecture binary index."""
        architecture = self.records[key].get('architecture', 'amd64')
        return qualifier in (None, 'any', 'native', architecture)

    def targets(self, atom, all_versions=False):
        """Resolve concrete versions and matching virtual providers."""
        name, architecture, operator, required = atom
        keys = [key for key in self.names.get(name, [])
                if self.architecture_matches(key, architecture)
                and satisfies(self.records[key]['version'], operator, required)]
        if keys and not all_versions:
            keys = [self.newest(keys)]
        keys.extend(self.virtual_targets(atom))
        return list(dict.fromkeys(keys))

    def virtual_targets(self, atom):
        """Match versioned Provides without using the provider's own version."""
        name, architecture, operator, required = atom
        keys = []
        for key, version in self.providers.get(name, []):
            if not self.architecture_matches(key, architecture):
                continue
            if operator and (version is None
                             or not satisfies(version, operator, required)):
                continue
            keys.append(key)
        return keys

    def newest(self, keys):
        """Choose the greatest Debian version, not lexicographic order."""
        versions = {self.records[key]['version']: key for key in keys}
        version = max(versions, key=cmp_to_key(compare_versions))
        return versions[version]

    def children(self, key):
        """Expand all available alternatives; fail unsatisfied OR groups."""
        result = []
        for declaration in self.direct(key):
            matches = []
            for atom in parse_group(declaration):
                matches.extend(self.targets(atom))
            if not matches:
                raise ValueError(f'{key}: unresolved dependency {declaration}')
            result.extend(matches)
        return list(dict.fromkeys(result))
