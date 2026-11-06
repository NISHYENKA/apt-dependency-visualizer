"""Produce PlantUML and display a locally rendered dependency diagram."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import webbrowser
from xml.etree import ElementTree


project_root = Path(__file__).resolve().parents[2]


def to_plantuml(graph):
    """Use synthetic IDs and quoted labels, keeping every graph edge."""
    ids = {node: f'n{index}' for index, node in enumerate(graph)}
    lines = ['@startuml', '!pragma layout smetana', 'left to right direction']
    for node in graph:
        label = json.dumps(node, ensure_ascii=True)
        lines.append(f'rectangle {label} as {ids[node]}')
    for parent, children in graph.items():
        for child in children:
            lines.append(f'{ids[parent]} --> {ids[child]}')
    return '\n'.join(lines + ['@enduml', ''])


def ascii_tree(graph, root):
    """Print branches once; distinguish ancestor cycles from shared nodes."""
    lines = []
    seen = set()
    stack = [(root, '', '', frozenset())]
    while stack:
        node, prefix, branch, ancestors = stack.pop()
        marker = node_marker(node, ancestors, seen)
        lines.append(prefix + branch + node + marker)
        if marker:
            continue
        seen.add(node)
        padding = '' if not branch else ('    ' if branch == '`-- ' else '|   ')
        children = graph[node]
        for index in reversed(range(len(children))):
            last = index == len(children) - 1
            stem = '`-- ' if last else '|-- '
            stack.append((children[index], prefix + padding, stem,
                          ancestors | {node}))
    return '\n'.join(lines)


def node_marker(node, ancestors, seen):
    """Give ancestor cycles precedence over shared-subgraph markers."""
    if node in ancestors:
        return ' [cycle]'
    return ' [shared]' if node in seen else ''


def render_svg(source):
    """Run local PlantUML with a timeout and validate its SVG output."""
    jar = project_root / 'tools' / 'plantuml.jar'
    java = shutil.which('java')
    if not java or not jar.is_file():
        raise ValueError('install Java and tools/plantuml.jar (see README)')
    command = [java, '-Djava.awt.headless=true', '-jar', str(jar),
               '-tsvg', '-pipe', '-charset', 'UTF-8']
    try:
        result = subprocess.run(command, input=source.encode(),
                                capture_output=True, timeout=120, check=False)
        root = ElementTree.fromstring(result.stdout)
    except (subprocess.TimeoutExpired, ElementTree.ParseError) as error:
        raise ValueError('PlantUML timeout or invalid SVG') from error
    if result.returncode or root.tag != '{http://www.w3.org/2000/svg}svg':
        detail = result.stderr.decode('utf-8', errors='replace')[:300]
        raise ValueError(f'PlantUML failed: {detail}')
    return result.stdout


def save_diagram(graph, package):
    """Publish successful SVG and PlantUML, then open the SVG in a browser."""
    source = to_plantuml(graph)
    svg = render_svg(source)
    folder = project_root / 'generated'
    folder.mkdir(exist_ok=True)
    destination = folder / f'{package}.svg'
    with tempfile.TemporaryDirectory(dir=folder) as temporary:
        image = Path(temporary) / 'graph.svg'
        image.write_bytes(svg)
        image.replace(destination)
    destination.with_suffix('.puml').write_text(source, encoding='utf-8')
    if not webbrowser.open(destination.as_uri()):
        print(f'Open the image manually: {destination}')
    return destination
