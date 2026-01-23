"""Data models for vault notes."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Valid roles in the vault
Role = Literal[
    "concept",
    "diagnostic",
    "domain",
    "projection",
    "registry",
    "paper",
    "meta",
    "support",
    "template",
]

# Valid layers for concepts
Layer = Literal[
    "primitive",
    "first-order",
    "accounting",
    "selector",
    "foundational",
    "failure-state",
    "meta-analytical",
]


@dataclass
class Note:
    """Base class for all vault notes."""

    path: Path
    name: str  # filename without extension
    content: str  # raw markdown after frontmatter
    frontmatter: dict  # parsed YAML
    role: str | None  # concept, diagnostic, domain, projection, etc.
    canonical: bool  # frontmatter.canonical
    links: list[str] = field(default_factory=list)  # all [[target]] references

    @property
    def title(self) -> str:
        """Extract title from first H1 header or use filename."""
        for line in self.content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
        return self.name


@dataclass
class Concept(Note):
    """A concept definition from /concepts."""

    layer: str = "unknown"  # primitive, first-order, accounting, etc.
    aliases: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)  # from Structural dependencies

    @property
    def is_primitive(self) -> bool:
        return self.layer == "primitive"


@dataclass
class Diagnostic(Note):
    """A diagnostic tool from /diagnostics."""

    depends_on: list[str] = field(default_factory=list)  # from frontmatter
    facets: list[str] = field(default_factory=list)


@dataclass
class Domain(Note):
    """A domain application from /domains."""

    transformation_space: str = ""
    candidate_differences: list[str] = field(default_factory=list)


@dataclass
class Projection(Note):
    """A projection/re-reading from /projections."""

    facets: list[str] = field(default_factory=list)
    projection_type: str = ""  # encoded, etc.


@dataclass
class Paper(Note):
    """A paper from /papers."""

    status: str = ""
    paper_type: str = ""
    depends_on: list[str] = field(default_factory=list)
