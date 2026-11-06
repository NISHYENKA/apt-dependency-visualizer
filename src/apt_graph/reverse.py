"""Build reverse relationships from the complete selected repository."""

from .relations import parse_group


def reverse_index(repository):
    """Invert all declared edges, matching every satisfying target version."""
    if hasattr(repository, 'graph'):
        forward = repository.graph
    else:
        forward = {}
        for parent in repository.records:
            children = []
            for group in repository.direct(parent):
                for atom in parse_group(group):
                    children.extend(repository.targets(atom, all_versions=True))
            forward[parent] = children
    reverse = {key: [] for key in forward}
    for parent, children in forward.items():
        for child in children:
            if parent not in reverse[child]:
                reverse[child].append(parent)
    return reverse
