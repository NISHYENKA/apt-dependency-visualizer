"""Download Ubuntu metadata using only Python's standard library."""

import gzip
from io import BytesIO
import lzma
from urllib.request import Request, urlopen

from .control import declarations, parse_packages


download_limit = 64 * 1024 * 1024
expanded_limit = 256 * 1024 * 1024


def unpack_index(data):
    """Recognize gzip/xz by magic bytes and bound decompressed size."""
    stream = BytesIO(data)
    if data.startswith(b'\x1f\x8b'):
        stream = gzip.GzipFile(fileobj=stream)
    elif data.startswith(b'\xfd7zXZ\x00'):
        stream = lzma.LZMAFile(stream)
    with stream:
        content = stream.read(expanded_limit + 1)
    if len(content) > expanded_limit:
        raise ValueError('expanded Packages index is too large')
    return content.decode('utf-8')


def download_index(url):
    """Download one Packages index with a timeout and size limit."""
    request = Request(url, headers={'User-Agent': 'apt-graph-coursework/1'})
    with urlopen(request, timeout=45) as response:
        data = response.read(download_limit + 1)
    if len(data) > download_limit:
        raise ValueError('downloaded Packages index is too large')
    return unpack_index(data)


class AptRepository:
    """Store all records of a single architecture/component index in memory."""

    def __init__(self, text):
        """Parse an already downloaded index without running apt or dpkg."""
        self.records = parse_packages(text)

    def root(self, name, version):
        """Require an exact version and show available versions on failure."""
        key = f'{name}@{version}'
        if key not in self.records:
            available = [item['version'] for item in self.records.values()
                         if item['package'] == name]
            raise ValueError(f'{key} not found; available: {available}')
        return key

    def direct(self, key):
        """Return direct declarations without discarding version constraints."""
        return declarations(self.records[key])
