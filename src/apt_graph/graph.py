"""Traverse breadth-first by recursively processing complete frontiers."""


def build_graph(root, children, max_depth):
    """Perform recursive BFS; each vertex is expanded at its shortest depth."""
    graph = {root: []}
    seen = {root}

    def visit_level(frontier, depth):
        """Expand a whole BFS frontier, then recurse to the next level."""
        if not frontier or depth >= max_depth:
            return
        following = []
        for node in frontier:
            graph[node] = list(dict.fromkeys(children(node)))
            for child in graph[node]:
                if child not in seen:
                    seen.add(child)
                    graph[child] = []
                    following.append(child)
        visit_level(following, depth + 1)

    visit_level([root], 0)
    return graph


def graph_lines(graph):
    """Show each vertex including isolated roots and boundary leaves."""
    return [f'{node} -> {", ".join(children) or "(none)"}'
            for node, children in graph.items()]
