"""Audit command - generate structural vault report from CSV exports.

Parses Obsidian Bases CSV exports and generates a Markdown report using the
irreversibility accounting framework vocabulary.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console


@dataclass
class ConceptRow:
    name: str
    layer: str
    depends_on: list[str]
    link_count: int = 0


@dataclass
class DomainRow:
    name: str
    primitives: dict[str, bool] = field(default_factory=dict)


@dataclass
class DiagnosticRow:
    name: str
    location: str
    has_dependencies: bool
    links: int


@dataclass
class ProjectionRow:
    name: str
    coverage: dict[str, bool] = field(default_factory=dict)


@dataclass
class InvariantRow:
    name: str
    role: str
    status: str
    canonical: bool
    links: int


@dataclass
class VaultNoteRow:
    name: str
    location: str
    modified: str
    outlinks: int
    tagged: bool


@dataclass
class AuditData:
    concepts: list[ConceptRow] = field(default_factory=list)
    domains: list[DomainRow] = field(default_factory=list)
    diagnostics: list[DiagnosticRow] = field(default_factory=list)
    projections: list[ProjectionRow] = field(default_factory=list)
    invariants: list[InvariantRow] = field(default_factory=list)
    vault_notes: list[VaultNoteRow] = field(default_factory=list)
    dependency_audit: list[ConceptRow] = field(default_factory=list)


def _extract_note_name(wikilink: str) -> str:
    """Extract note name from wikilink like [[path/name.md|display]]."""
    match = re.search(r'\[\[([^\]|]+?)(?:\.md)?\|([^\]]+)\]\]', wikilink)
    if match:
        return match.group(2)
    match = re.search(r'\[\[([^\]]+)\]\]', wikilink)
    if match:
        return match.group(1).split('|')[-1].replace('.md', '')
    return wikilink.strip()


def _parse_wikilink_list(cell: str) -> list[str]:
    """Parse a cell containing comma-separated wikilinks."""
    if not cell or cell.strip() == '':
        return []
    links = re.findall(r'\[\[[^\]]+\]\]', cell)
    return [_extract_note_name(link) for link in links]


def _parse_yes_no(val: str) -> bool:
    """Parse yes/no to bool."""
    return val.strip().lower() == 'yes'


def _load_concept_topology(path: Path) -> list[ConceptRow]:
    """Load Concept topology.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(ConceptRow(
                name=_extract_note_name(row.get('concept', '')),
                layer=row.get('layer', 'unknown'),
                depends_on=_parse_wikilink_list(row.get('depends_on', '')),
            ))
    return rows


def _load_dependency_audit(path: Path) -> list[ConceptRow]:
    """Load Dependency audit.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(ConceptRow(
                name=_extract_note_name(row.get('concept', '')),
                layer='',
                depends_on=_parse_wikilink_list(row.get('depends_on', '')),
                link_count=int(row.get('links', 0) or 0),
            ))
    return rows


def _load_primitive_coverage(path: Path) -> list[DomainRow]:
    """Load Primitive coverage audit.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            primitives = {}
            for key in row:
                if key != 'domain_note':
                    primitives[key] = _parse_yes_no(row[key])
            rows.append(DomainRow(
                name=_extract_note_name(row.get('domain_note', '')),
                primitives=primitives,
            ))
    return rows


def _load_diagnostics(path: Path) -> list[DiagnosticRow]:
    """Load Diagnostics inventory.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(DiagnosticRow(
                name=_extract_note_name(row.get('diagnostic', '')),
                location=row.get('location', ''),
                has_dependencies=_parse_yes_no(row.get('has_dependencies', 'no')),
                links=int(row.get('links', 0) or 0),
            ))
    return rows


def _load_projections(path: Path) -> list[ProjectionRow]:
    """Load Projections.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coverage = {}
            skip_keys = {'projection', 'tags'}
            for key in row:
                if key not in skip_keys:
                    coverage[key] = _parse_yes_no(row[key])
            rows.append(ProjectionRow(
                name=_extract_note_name(row.get('projection', '')),
                coverage=coverage,
            ))
    return rows


def _load_invariants(path: Path) -> list[InvariantRow]:
    """Load Invariants inventory.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(InvariantRow(
                name=_extract_note_name(row.get('invariant', '')),
                role=row.get('role', ''),
                status=row.get('status', ''),
                canonical=_parse_yes_no(row.get('canonical', 'no')),
                links=int(row.get('links', 0) or 0),
            ))
    return rows


def _load_vault_audit(path: Path) -> list[VaultNoteRow]:
    """Load Full vault audit.csv."""
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(VaultNoteRow(
                name=_extract_note_name(row.get('note', '')),
                location=row.get('location', ''),
                modified=row.get('modified', ''),
                outlinks=int(row.get('outlinks', 0) or 0),
                tagged=_parse_yes_no(row.get('tagged', 'no')),
            ))
    return rows


def load_audit_data(csv_folder: Path) -> AuditData:
    """Load all CSV exports from a folder."""
    data = AuditData()

    mappings = [
        ('Concept topology.csv', lambda p: setattr(data, 'concepts', _load_concept_topology(p))),
        ('Dependency audit.csv', lambda p: setattr(data, 'dependency_audit', _load_dependency_audit(p))),
        ('Primitive coverage audit.csv', lambda p: setattr(data, 'domains', _load_primitive_coverage(p))),
        ('Diagnostics inventory.csv', lambda p: setattr(data, 'diagnostics', _load_diagnostics(p))),
        ('Projections.csv', lambda p: setattr(data, 'projections', _load_projections(p))),
        ('Invariants inventory.csv', lambda p: setattr(data, 'invariants', _load_invariants(p))),
        ('Full vault audit.csv', lambda p: setattr(data, 'vault_notes', _load_vault_audit(p))),
    ]

    for filename, loader in mappings:
        path = csv_folder / filename
        if path.exists():
            loader(path)

    return data


def _count_layers(concepts: list[ConceptRow]) -> dict[str, int]:
    """Count concepts by layer."""
    counts: dict[str, int] = {}
    for c in concepts:
        counts[c.layer] = counts.get(c.layer, 0) + 1
    return counts


def _find_orphans(vault_notes: list[VaultNoteRow]) -> list[VaultNoteRow]:
    """Find notes with 0 outlinks."""
    return [n for n in vault_notes if n.outlinks == 0]


def _find_high_link_notes(vault_notes: list[VaultNoteRow], threshold: int = 20) -> list[VaultNoteRow]:
    """Find notes with high outlink counts."""
    return sorted([n for n in vault_notes if n.outlinks >= threshold], key=lambda x: -x.outlinks)


def _find_domain_gaps(domains: list[DomainRow]) -> dict[str, list[str]]:
    """Find missing primitive links per domain."""
    gaps: dict[str, list[str]] = {}
    for d in domains:
        missing = [k for k, v in d.primitives.items() if not v]
        if missing:
            gaps[d.name] = missing
    return gaps


def generate_report(data: AuditData) -> str:
    """Generate the Markdown audit report."""
    lines: list[str] = []
    now = datetime.now().strftime('%Y-%m-%d')

    lines.append('# Vault Structural Audit Report')
    lines.append('')
    lines.append(f'> **Generated:** {now}')
    lines.append('> **Scope:** Full vault integrity analysis using the irreversibility accounting framework')
    lines.append('> **Non-claim:** This report surfaces structural patterns and constraint-load signals. It does not prescribe action.')
    lines.append('')
    lines.append('---')
    lines.append('')

    # Executive summary
    total_notes = len(data.vault_notes)
    orphans = _find_orphans(data.vault_notes)
    high_link = _find_high_link_notes(data.vault_notes)
    domain_gaps = _find_domain_gaps(data.domains)
    diag_no_deps = [d for d in data.diagnostics if not d.has_dependencies]
    proj_missing_fm = [p for p in data.projections if not p.coverage.get('failure_modes', True)]

    lines.append('## Executive Summary')
    lines.append('')
    lines.append(f'The vault contains **{total_notes} notes** across content folders. ')
    lines.append('The audit reveals specific **constraint-load accumulation points** and **routing pressure** that merit attention.')
    lines.append('')
    lines.append('### Key Findings')
    lines.append('')
    lines.append('| Signal | Count | Interpretation |')
    lines.append('|--------|-------|----------------|')
    lines.append(f'| Orphan notes (0 outlinks) | {len(orphans)} | Potential accounting-failure: unintegrated content |')
    lines.append(f'| High-link notes (20+) | {len(high_link)} | Hub candidates; may carry disproportionate constraint load |')
    lines.append(f'| Domains with primitive gaps | {len(domain_gaps)}/{len(data.domains)} | Missing foundational concept links |')
    lines.append(f'| Diagnostics without dependencies | {len(diag_no_deps)} | May not properly trace to concept graph |')
    lines.append(f'| Projections missing failure_modes | {len(proj_missing_fm)}/{len(data.projections)} | Incomplete failure mode documentation |')
    lines.append('')
    lines.append('---')
    lines.append('')

    # Concept graph topology
    if data.concepts:
        lines.append('## 1. Concept Graph Topology')
        lines.append('')
        lines.append('### Layer Distribution')
        lines.append('')
        layer_counts = _count_layers(data.concepts)
        lines.append('| Layer | Count |')
        lines.append('|-------|-------|')
        for layer, count in sorted(layer_counts.items(), key=lambda x: -x[1]):
            lines.append(f'| {layer} | {count} |')
        lines.append('')

    # Hub spine (high outlink concepts)
    if data.dependency_audit:
        lines.append('### Hub Spine (high outlink concepts)')
        lines.append('')
        lines.append('These concepts carry the highest **dependency count** (outlinks), indicating they route through many other concepts:')
        lines.append('')
        lines.append('| Concept | Outlinks | Key Dependencies |')
        lines.append('|---------|----------|------------------|')
        top_deps = sorted(data.dependency_audit, key=lambda x: -x.link_count)[:10]
        for c in top_deps:
            deps_str = ', '.join(c.depends_on[:5])
            if len(c.depends_on) > 5:
                deps_str += f' (+{len(c.depends_on) - 5} more)'
            lines.append(f'| [[{c.name}]] | {c.link_count} | {deps_str} |')
        lines.append('')
        lines.append('**Interpretation:** These concepts function as **routing junctions**. Changes to their definitions propagate constraint-load downstream.')
        lines.append('')
        lines.append('---')
        lines.append('')

    # Domain primitive coverage
    if data.domains:
        lines.append('## 2. Domain Primitive Coverage Audit')
        lines.append('')
        if domain_gaps:
            lines.append('The following domains are missing links to primitive concepts:')
            lines.append('')
            # Build header from all primitive keys
            all_primitives = set()
            for d in data.domains:
                all_primitives.update(d.primitives.keys())
            primitives_list = sorted(all_primitives)

            header = '| Domain |' + '|'.join(f' {p} ' for p in primitives_list) + '|'
            sep = '|--------|' + '|'.join('---' for _ in primitives_list) + '|'
            lines.append(header)
            lines.append(sep)
            for d in data.domains:
                cells = []
                for p in primitives_list:
                    val = d.primitives.get(p, False)
                    cells.append('yes' if val else '**no**')
                lines.append(f'| {d.name} |' + '|'.join(cells) + '|')
            lines.append('')
            lines.append('### Structural Diagnosis')
            lines.append('')
            lines.append('Missing primitive links suggest **systematic omission** rather than domain-specific reasoning. ')
            lines.append('Each domain note should explicitly link to foundational primitives to prevent accounting-failure.')
            lines.append('')
        else:
            lines.append('All domains have complete primitive coverage.')
            lines.append('')
        lines.append('---')
        lines.append('')

    # Orphan and high-link notes
    lines.append('## 3. Orphan and High-Link Notes')
    lines.append('')

    if orphans:
        lines.append('### Orphan Notes (0 outlinks)')
        lines.append('')
        lines.append('| Note | Location | Modified |')
        lines.append('|------|----------|----------|')
        for n in orphans:
            lines.append(f'| {n.name} | {n.location} | {n.modified[:10] if n.modified else ""} |')
        lines.append('')
        lines.append('**Interpretation:** These notes have no internal links to the concept graph. They may be stubs, external references, or accounting-failures.')
        lines.append('')
    else:
        lines.append('No orphan notes detected.')
        lines.append('')

    if high_link:
        lines.append('### High-Link Notes (20+ outlinks)')
        lines.append('')
        lines.append('| Note | Location | Outlinks |')
        lines.append('|------|----------|----------|')
        for n in high_link[:10]:
            lines.append(f'| {n.name} | {n.location} | {n.outlinks} |')
        lines.append('')
        lines.append('**Interpretation:** High-link notes function as **reference hubs** or densely connected documents.')
        lines.append('')

    lines.append('---')
    lines.append('')

    # Diagnostics inventory
    if data.diagnostics:
        lines.append('## 4. Diagnostics Inventory')
        lines.append('')

        # Group by location
        by_location: dict[str, list[DiagnosticRow]] = {}
        for d in data.diagnostics:
            by_location.setdefault(d.location, []).append(d)

        lines.append('### By Subfolder')
        lines.append('')
        lines.append('| Location | Count | Total Links |')
        lines.append('|----------|-------|-------------|')
        for loc, diags in sorted(by_location.items()):
            total_links = sum(d.links for d in diags)
            lines.append(f'| {loc} | {len(diags)} | {total_links} |')
        lines.append('')

        if diag_no_deps:
            lines.append('### Diagnostics Without Dependencies')
            lines.append('')
            lines.append('| Diagnostic | Links |')
            lines.append('|------------|-------|')
            for d in diag_no_deps:
                lines.append(f'| **{d.name}** | {d.links} |')
            lines.append('')
            lines.append('**Signal:** Diagnostics without declared dependencies may not properly trace to the concept graph.')
            lines.append('')

        lines.append('---')
        lines.append('')

    # Projections coverage
    if data.projections:
        lines.append('## 5. Projections Coverage')
        lines.append('')

        # Build coverage table
        all_coverage_keys = set()
        for p in data.projections:
            all_coverage_keys.update(p.coverage.keys())
        coverage_keys = sorted(all_coverage_keys)

        lines.append('### Core Concept Linkage')
        lines.append('')
        header = '| Projection |' + '|'.join(f' {k} ' for k in coverage_keys) + '|'
        sep = '|------------|' + '|'.join('---' for _ in coverage_keys) + '|'
        lines.append(header)
        lines.append(sep)
        for p in data.projections:
            cells = []
            for k in coverage_keys:
                val = p.coverage.get(k, False)
                cells.append('yes' if val else 'no')
            lines.append(f'| {p.name} |' + '|'.join(cells) + '|')
        lines.append('')

        # Pattern analysis
        all_covered = [k for k in coverage_keys if all(p.coverage.get(k, False) for p in data.projections)]
        if all_covered:
            lines.append(f'**All projections** link to: {", ".join(all_covered)}')
            lines.append('')

        lines.append('---')
        lines.append('')

    # Invariants integrity
    if data.invariants:
        lines.append('## 6. Invariants Integrity')
        lines.append('')
        lines.append('| Invariant | Role | Status | Canonical | Links |')
        lines.append('|-----------|------|--------|-----------|-------|')
        for inv in data.invariants:
            canonical = 'yes' if inv.canonical else 'no'
            lines.append(f'| {inv.name} | {inv.role} | {inv.status} | {canonical} | {inv.links} |')
        lines.append('')

        all_canonical = all(inv.canonical for inv in data.invariants)
        if all_canonical:
            lines.append('All invariants are properly marked as canonical and structural.')
        lines.append('')
        lines.append('---')
        lines.append('')

    # Constraint-load summary
    lines.append('## 7. Constraint-Load Summary')
    lines.append('')
    lines.append('### Where cost accumulates')
    lines.append('')
    if domain_gaps:
        lines.append(f'1. **Domain notes**: {len(domain_gaps)} domains have missing primitive links, creating implicit dependencies.')
    if diag_no_deps:
        lines.append(f'2. **Disconnected diagnostics**: {len(diag_no_deps)} diagnostics without dependency declarations.')
    if orphans:
        lines.append(f'3. **Orphan notes**: {len(orphans)} notes carry no graph weight.')
    lines.append('')

    lines.append('### Routing pressure points')
    lines.append('')
    if data.dependency_audit:
        top3 = sorted(data.dependency_audit, key=lambda x: -x.link_count)[:3]
        for i, c in enumerate(top3, 1):
            lines.append(f'{i}. **{c.name}** ({c.link_count} links): High-dependency hub.')
    lines.append('')
    lines.append('---')
    lines.append('')

    # Recommended actions
    lines.append('## 8. Recommended Actions')
    lines.append('')
    lines.append('### High Priority (prevent accounting-failure)')
    lines.append('')
    action_num = 1
    if domain_gaps:
        lines.append(f'{action_num}. **Domain primitive completion**: Add explicit links to missing primitives in domain notes')
        action_num += 1
    if diag_no_deps:
        lines.append(f'{action_num}. **Diagnostic dependencies**: Add depends_on frontmatter to disconnected diagnostics')
        action_num += 1
    if orphans:
        lines.append(f'{action_num}. **Orphan integration**: Either link orphan notes to concept graph or mark as external-only')
        action_num += 1
    lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('## Appendix: Data Sources')
    lines.append('')
    lines.append('This report synthesizes exports from Obsidian Bases CSV files.')
    lines.append(f'Generated {now}.')
    lines.append('')

    return '\n'.join(lines)


def run_audit(
    csv_folder: Path,
    *,
    out: Path | None = None,
) -> int:
    """Run the audit command.

    Args:
        csv_folder: Path to folder containing CSV exports
        out: Optional output file path; prints to stdout if None

    Returns:
        Exit code (0 for success)
    """
    console = Console(stderr=True)

    if not csv_folder.exists():
        console.print(f"[red]CSV folder not found: {csv_folder}[/red]")
        return 1

    if not csv_folder.is_dir():
        console.print(f"[red]Not a directory: {csv_folder}[/red]")
        return 1

    # Check for at least one expected CSV
    expected_csvs = [
        'Concept topology.csv',
        'Full vault audit.csv',
    ]
    found = any((csv_folder / name).exists() for name in expected_csvs)
    if not found:
        console.print(f"[yellow]Warning: No expected CSV files found in {csv_folder}[/yellow]")
        console.print("Expected at least one of: " + ", ".join(expected_csvs))

    data = load_audit_data(csv_folder)
    report = generate_report(data)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding='utf-8')
        console.print(f"[green]Wrote audit report to {out}[/green]")
    else:
        print(report)

    return 0
