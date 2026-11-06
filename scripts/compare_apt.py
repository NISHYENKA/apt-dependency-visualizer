"""Independent Linux validation; apt-cache is not an application dependency."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.apt_graph.config import default_repository
from src.apt_graph.graph import build_graph
from src.apt_graph.repository import download_index
from src.apt_graph.resolver import ResolvedRepository


def apt_command(directory, packages):
    """Build an isolated APT cache containing only the downloaded index."""
    sources = directory / 'sources.list'
    sources.write_text('deb [trusted=yes] http://localhost/ubuntu noble main\n',
                       encoding='utf-8')
    options = {'Dir::State::lists': str(directory / 'lists'),
               'Dir::State::status': '/dev/null',
               'Dir::Cache::pkgcache': '', 'Dir::Cache::srcpkgcache': '',
               'Dir::Etc::sourcelist': str(sources),
               'Dir::Etc::sourceparts': '-', 'APT::Architecture': 'amd64'}
    (directory / 'lists').mkdir()
    index = 'localhost_ubuntu_dists_noble_main_binary-amd64_Packages'
    (directory / 'lists' / index).write_bytes(packages.read_bytes())
    command = ['apt-cache']
    for key, value in options.items():
        command.extend(['-o', f'{key}={value}'])
    return command


def run_apt(command, arguments):
    """Execute an external reference command and retain its plain output."""
    result = subprocess.run(command + arguments, capture_output=True,
                            text=True, timeout=90, check=False,
                            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    if result.returncode:
        raise ValueError(f'apt-cache {arguments}: {result.stderr}')
    return result.stdout


def concrete_dependencies(text):
    """Normalize apt-cache important dependencies, expanding virtual names."""
    children = set()
    for line in text.splitlines():
        match = re.match(r'\s*\|?(?:PreDepends|Depends):\s+(\S+)', line)
        if match:
            name = match.group(1)
            if not name.startswith('<'):
                children.add(name.split(':')[0])
        elif line.startswith('    ') and line.strip():
            children.add(line.strip().split()[0].split(':')[0])
    return children


def compare_package(command, repository, name, output):
    """Compare every expanded edge to apt-cache and retain native DOT."""
    root = repository.newest(repository.names[name])
    graph = build_graph(root, repository.children, 200)
    for parent, children in graph.items():
        package, version = parent.split('@', 1)
        raw = run_apt(command, ['depends', '--important',
                                f'{package}={version}'])
        expected = {child.split('@', 1)[0] for child in children}
        actual = concrete_dependencies(raw)
        if expected != actual:
            raise AssertionError((parent, expected, actual, raw))
    dot = run_apt(command, ['dotty', name])
    (output / f'{name}-apt.dot').write_text(dot, encoding='utf-8')
    direct = run_apt(command, ['depends', '--important', name])
    (output / f'{name}-apt.txt').write_text(direct, encoding='utf-8')
    record = {'root': root, 'vertices': len(graph),
              'edges': sum(map(len, graph.values())), 'edge_match': True,
              'dot_edges': len(re.findall(r'"[^"]+"\s*->', dot))}
    print(json.dumps(record), flush=True)
    return record


def main():
    """Download one index for both implementations and compare three roots."""
    output = Path('generated/comparison')
    output.mkdir(parents=True, exist_ok=True)
    text = download_index(default_repository)
    repository = ResolvedRepository(text)
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        packages = directory / 'Packages'
        packages.write_text(text, encoding='utf-8')
        command = apt_command(directory, packages)
        records = [compare_package(command, repository, name, output)
                   for name in ('bash', 'coreutils', 'grep')]
    (output / 'results.json').write_text(json.dumps(records, indent=2),
                                         encoding='utf-8')


if __name__ == '__main__':
    main()
