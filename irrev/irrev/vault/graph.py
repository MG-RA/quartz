"""Dependency graph construction and analysis."""

from collections import defaultdict
from dataclasses import dataclass, field

from ..models import Concept


@dataclass
class DependencyGraph:
    """Graph of concept dependencies with cycle detection and traversal."""

    nodes: dict[str, Concept] = field(default_factory=dict)  # name -> Concept
    aliases: dict[str, str] = field(default_factory=dict)  # alias -> canonical name
    edges: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )  # concept -> dependencies
    reverse_edges: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )  # concept -> dependents

    @classmethod
    def from_concepts(
        cls, concepts: list[Concept], aliases: dict[str, str] | None = None
    ) -> "DependencyGraph":
        """Build graph from list of concepts."""
        graph = cls()
        graph.aliases = aliases or {}

        # Add all nodes first
        for concept in concepts:
            canonical = concept.name.lower()
            graph.nodes[canonical] = concept

            # Add aliases for this concept
            for alias in concept.aliases:
                graph.aliases[alias.lower()] = canonical

        # Build edges
        for concept in concepts:
            src = concept.name.lower()
            for dep in concept.depends_on:
                dst = graph.normalize(dep)
                graph.edges[src].add(dst)
                graph.reverse_edges[dst].add(src)

        return graph

    def normalize(self, name: str) -> str:
        """Normalize a name to its canonical form."""
        normalized = name.lower()
        return self.aliases.get(normalized, normalized)

    def get_dependencies(self, name: str) -> set[str]:
        """Get direct dependencies of a concept."""
        return self.edges.get(self.normalize(name), set())

    def get_dependents(self, name: str) -> set[str]:
        """Get concepts that depend on this one."""
        return self.reverse_edges.get(self.normalize(name), set())

    def transitive_closure(self, start: str) -> set[str]:
        """Get all dependencies reachable from start (for pack command).

        Returns set of canonical names including the start node.
        """
        normalized = self.normalize(start)
        visited = set()
        stack = [normalized]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            for dep in self.edges.get(current, set()):
                if dep not in visited:
                    stack.append(dep)

        return visited

    def topological_sort(self) -> list[str]:
        """Return concepts in dependency order (deps first).

        Uses Kahn's algorithm. Returns partial order if cycles exist.
        """
        # Calculate in-degrees
        in_degree = {node: 0 for node in self.nodes}
        for src, deps in self.edges.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[src] = in_degree.get(src, 0)  # ensure src exists

        for deps in self.edges.values():
            for dep in deps:
                if dep in self.nodes:
                    pass  # in_degree already initialized

        # Recalculate properly
        in_degree = {node: 0 for node in self.nodes}
        for src, deps in self.edges.items():
            for dep in deps:
                if src in in_degree:
                    # src depends on dep, so src's in_degree increases
                    pass  # Actually we need reverse logic

        # Let's use correct Kahn's: in_degree[x] = number of things x depends on
        in_degree = defaultdict(int)
        for node in self.nodes:
            in_degree[node] = len(
                [d for d in self.edges.get(node, set()) if d in self.nodes]
            )

        # Start with nodes that have no dependencies
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # For each node that depends on this one, decrement its in_degree
            for dependent in self.reverse_edges.get(node, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def find_cycles(self) -> list[list[str]]:
        """Find all cycles using Tarjan's strongly connected components.

        Returns list of cycles (each cycle is a list of node names).
        Only returns SCCs with more than one node (actual cycles).
        """
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for dep in self.edges.get(node, set()):
                if dep not in self.nodes:
                    continue  # Skip external references
                if dep not in index:
                    strongconnect(dep)
                    lowlinks[node] = min(lowlinks[node], lowlinks[dep])
                elif on_stack.get(dep, False):
                    lowlinks[node] = min(lowlinks[node], index[dep])

            if lowlinks[node] == index[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break
                if len(scc) > 1:
                    sccs.append(scc)

        for node in self.nodes:
            if node not in index:
                strongconnect(node)

        return sccs

    def find_simple_cycles(self) -> list[list[str]]:
        """Find simple cycles (for clearer error messages).

        Returns cycles as ordered paths from A -> B -> ... -> A.
        """
        cycles = []
        visited = set()

        def dfs(node, path):
            if node in path:
                # Found cycle - extract it
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            path.append(node)
            for dep in self.edges.get(node, set()):
                if dep in self.nodes:
                    dfs(dep, path.copy())

            visited.add(node)

        for node in self.nodes:
            if node not in visited:
                dfs(node, [])

        # Deduplicate cycles (same cycle can be found from different starts)
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            # Normalize cycle by rotating to start with smallest element
            if len(cycle) > 1:
                min_idx = cycle[:-1].index(min(cycle[:-1]))
                normalized = tuple(cycle[min_idx:-1]) + tuple(cycle[:min_idx]) + (cycle[min_idx],)
                if normalized not in seen:
                    seen.add(normalized)
                    unique_cycles.append(list(normalized))

        return unique_cycles
