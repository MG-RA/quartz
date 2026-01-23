"""Vault loading and note categorization."""

from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from ..models import Concept, Diagnostic, Domain, Note, Paper, Projection
from .parser import (
    extract_frontmatter_depends_on,
    extract_links,
    extract_structural_dependencies,
)


@dataclass
class Vault:
    """Container for all loaded vault notes."""

    path: Path
    concepts: list[Concept] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    domains: list[Domain] = field(default_factory=list)
    projections: list[Projection] = field(default_factory=list)
    papers: list[Paper] = field(default_factory=list)
    meta: list[Note] = field(default_factory=list)
    support: list[Note] = field(default_factory=list)

    # Lookup tables built after loading
    _by_name: dict[str, Note] = field(default_factory=dict)
    _aliases: dict[str, str] = field(default_factory=dict)  # alias -> canonical name

    def __post_init__(self):
        self._build_lookups()

    def _build_lookups(self):
        """Build name lookup and alias mapping."""
        all_notes = (
            self.concepts
            + self.diagnostics
            + self.domains
            + self.projections
            + self.papers
            + self.meta
            + self.support
        )

        for note in all_notes:
            self._by_name[note.name.lower()] = note

        # Build alias mapping from concepts
        for concept in self.concepts:
            canonical = concept.name.lower()
            for alias in concept.aliases:
                self._aliases[alias.lower()] = canonical

    def get(self, name: str) -> Note | None:
        """Get note by name or alias."""
        normalized = name.lower()
        # Check alias first
        if normalized in self._aliases:
            normalized = self._aliases[normalized]
        return self._by_name.get(normalized)

    def normalize_name(self, name: str) -> str:
        """Normalize a name to its canonical form."""
        normalized = name.lower()
        return self._aliases.get(normalized, normalized)

    @property
    def all_notes(self) -> list[Note]:
        """All notes in the vault."""
        return (
            self.concepts
            + self.diagnostics
            + self.domains
            + self.projections
            + self.papers
            + self.meta
            + self.support
        )


def infer_role_from_path(path: Path, vault_path: Path) -> str | None:
    """Infer note role from its path relative to vault."""
    try:
        rel = path.relative_to(vault_path)
        parts = rel.parts
    except ValueError:
        return None

    if not parts:
        return None

    folder = parts[0].lower()
    role_map = {
        "concepts": "concept",
        "diagnostics": "diagnostic",
        "domains": "domain",
        "projections": "projection",
        "papers": "paper",
        "meta": "meta",
        "support": "support",
    }
    return role_map.get(folder)


def load_note(path: Path, vault_path: Path) -> Note:
    """Load a single markdown file and parse its frontmatter."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or infer_role_from_path(path, vault_path)
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    return Note(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
    )


def load_concept(path: Path, vault_path: Path) -> Concept:
    """Load a concept note with its layer and dependencies."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or "concept"
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    layer = fm.get("layer", "unknown")
    aliases = fm.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]

    depends_on = extract_structural_dependencies(content)

    return Concept(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
        layer=layer,
        aliases=aliases,
        depends_on=depends_on,
    )


def load_diagnostic(path: Path, vault_path: Path) -> Diagnostic:
    """Load a diagnostic note with its dependencies."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or "diagnostic"
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    depends_on = extract_frontmatter_depends_on(fm)
    facets = fm.get("facets", [])

    return Diagnostic(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
        depends_on=depends_on,
        facets=facets,
    )


def load_domain(path: Path, vault_path: Path) -> Domain:
    """Load a domain application note."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or "domain"
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    # TODO: Extract transformation_space and candidate_differences from content

    return Domain(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
    )


def load_projection(path: Path, vault_path: Path) -> Projection:
    """Load a projection note."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or "projection"
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    facets = fm.get("facets", [])
    projection_type = fm.get("type", "")

    return Projection(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
        facets=facets,
        projection_type=projection_type,
    )


def load_paper(path: Path, vault_path: Path) -> Paper:
    """Load a paper note."""
    post = frontmatter.load(path)

    name = path.stem
    content = post.content
    fm = post.metadata

    role = fm.get("role") or "paper"
    canonical = fm.get("canonical", False)
    links = extract_links(content)

    depends_on = extract_frontmatter_depends_on(fm)

    return Paper(
        path=path,
        name=name,
        content=content,
        frontmatter=fm,
        role=role,
        canonical=canonical,
        links=links,
        depends_on=depends_on,
    )


def load_vault(vault_path: Path) -> Vault:
    """Load all markdown files from the vault.

    Args:
        vault_path: Path to the vault content directory

    Returns:
        Vault object with all notes categorized
    """
    vault = Vault(path=vault_path)

    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and directories
        if any(part.startswith(".") for part in md_file.parts):
            continue

        role = infer_role_from_path(md_file, vault_path)

        try:
            if role == "concept":
                vault.concepts.append(load_concept(md_file, vault_path))
            elif role == "diagnostic":
                vault.diagnostics.append(load_diagnostic(md_file, vault_path))
            elif role == "domain":
                vault.domains.append(load_domain(md_file, vault_path))
            elif role == "projection":
                vault.projections.append(load_projection(md_file, vault_path))
            elif role == "paper":
                vault.papers.append(load_paper(md_file, vault_path))
            elif role == "meta":
                vault.meta.append(load_note(md_file, vault_path))
            elif role == "support":
                vault.support.append(load_note(md_file, vault_path))
            else:
                # Root-level files or unknown
                vault.meta.append(load_note(md_file, vault_path))
        except Exception as e:
            # Log error but continue loading
            print(f"Warning: Failed to load {md_file}: {e}")

    # Build lookups after loading
    vault._build_lookups()

    return vault
