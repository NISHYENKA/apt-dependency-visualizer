"""Compare Debian epoch:upstream-revision versions without dpkg libraries."""

import re


zero = 0


def split_version(text):
    """Split epoch and final Debian revision, validating version syntax."""
    if not re.fullmatch(r'(?:[0-9]+:)?[0-9][A-Za-z0-9.+:~\-]*', text):
        raise ValueError(f'invalid Debian version: {text}')
    epoch = 0
    if ':' in text:
        prefix, text = text.split(':', 1)
        epoch = int(prefix)
    upstream, dash, revision = text.rpartition('-')
    return epoch, upstream if dash else text, revision if dash else '0'


def character_order(char):
    """Sort tilde before end, letters before all other non-digit symbols."""
    if char == '~':
        return -1
    if not char or char.isdigit():
        return 0
    return ord(char) if char.isalpha() else ord(char) + 256


def compare_part(left, right):
    """Compare alternating nondigit and digit runs using Debian rules."""
    while left or right:
        while (left and not left[0].isdigit()
               or right and not right[0].isdigit()):
            first = character_order(left[:1])
            second = character_order(right[:1])
            if first != second:
                return (first > second) - (first < second)
            left, right = left[1:], right[1:]
        digits_left = re.match(r'[0-9]*', left).group()
        digits_right = re.match(r'[0-9]*', right).group()
        first = digits_left.lstrip('0')
        second = digits_right.lstrip('0')
        key_left, key_right = (len(first), first), (len(second), second)
        if key_left != key_right:
            return (key_left > key_right) - (key_left < key_right)
        left = left[len(digits_left):]
        right = right[len(digits_right):]
    return 0


def compare_versions(left, right):
    """Compare epochs, upstream versions, then Debian revisions."""
    epoch_left, upstream_left, revision_left = split_version(left)
    epoch_right, upstream_right, revision_right = split_version(right)
    if epoch_left != epoch_right:
        return (epoch_left > epoch_right) - (epoch_left < epoch_right)
    return (compare_part(upstream_left, upstream_right)
            or compare_part(revision_left, revision_right))


def satisfies(version, operator, required):
    """Evaluate the five Debian relationship operators."""
    if not operator:
        return True
    value = compare_versions(version, required)
    results = {'<<': value < zero, '<=': value <= zero, '=': value == zero,
               '>=': value >= zero, '>>': value > zero}
    if operator not in results:
        raise ValueError(f'unknown version operator: {operator}')
    return results[operator]
