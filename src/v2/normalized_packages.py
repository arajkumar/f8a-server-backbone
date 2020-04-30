"""Abstraction for various response models used in V2 implementation."""

from collections import defaultdict
from typing import List, Tuple, Dict, Set
from src.v2.models import Package, Ecosystem

class NormalizedPackages:
    """Duplicate free Package List."""

    def __init__(self, packages: List[Package], ecosystem: Ecosystem):
        """Create NormalizedPackages by removing all duplicates from packages."""
        self._packages = packages
        self._ecosystem = ecosystem
        self._dependency_graph: Dict[Package, Set[Package]] = defaultdict(set)
        for package in packages:
            self._dependency_graph[package] = self._dependency_graph[package] or set()
            for trans_package in package.dependencies or []:
                self._dependency_graph[package].add(trans_package)
        # unfold set of Package into flat set of Package
        self._transtives: Set[Package] = {d for dep in self._dependency_graph.values() for d in dep}
        self._directs = frozenset(self._dependency_graph.keys())
        self._all = self._directs.union(self._transtives)

    @property
    def direct_dependencies(self) -> Tuple[Package]:
        """Immutable list of direct dependency Package."""
        return tuple(self._directs)

    @property
    def transitive_dependencies(self) -> Tuple[Package]:
        """Immutable list of transitives dependency Package."""
        return tuple(self._transtives)

    @property
    def all_dependencies(self) -> Tuple[Package]:
        """Union of all direct and transitives without duplicates."""
        return tuple(self._all)

    @property
    def dependency_graph(self) -> Dict[Package, Set[Package]]:
        """Package with it's transtive without duplicates."""
        return self._dependency_graph

    @property
    def ecosystem(self):
        """Ecosystem value."""
        return self._ecosystem
