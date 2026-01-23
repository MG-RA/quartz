"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import Vault, load_vault


@pytest.fixture
def fixture_vault_path() -> Path:
    """Path to the minimal fixture vault."""
    return Path(__file__).parent / "fixtures" / "minimal_vault"


@pytest.fixture
def fixture_vault(fixture_vault_path: Path) -> Vault:
    """Load the minimal fixture vault."""
    return load_vault(fixture_vault_path)


@pytest.fixture
def fixture_graph(fixture_vault: Vault) -> DependencyGraph:
    """Build dependency graph from fixture vault."""
    return DependencyGraph.from_concepts(fixture_vault.concepts, fixture_vault._aliases)
