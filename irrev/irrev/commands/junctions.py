"""Junctions command group - detect routing pressure and missing concepts.

Phase 1 focuses on an inside-out concept audit: surface load-bearing concepts and
definition hygiene issues from the existing concept graph.

Phase 1b adds definition semantic analysis: verb patterns, implicit dependencies,
role purity signals, and definition scope metrics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault


# -----------------------------------------------------------------------------
# Verb and pattern word lists (Phase 1b)
# -----------------------------------------------------------------------------

STATE_VERBS = frozenset({
    "remains", "persists", "exists", "is", "are", "was", "were", "stays", "continues",
    "remain", "persist", "exist", "stay", "continue",
})

ACTION_VERBS = frozenset({
    "removes", "constrains", "eliminates", "narrows", "forecloses", "reduces",
    "blocks", "prevents", "restricts", "remove", "constrain", "eliminate",
    "narrow", "foreclose", "reduce", "block", "prevent", "restrict",
})

MODAL_VERBS = frozenset({
    "can", "cannot", "must", "may", "might", "should", "could", "would", "requires",
    "require",
})

CAUSAL_VERBS = frozenset({
    "causes", "produces", "transforms", "converts", "creates", "generates",
    "leads", "results", "cause", "produce", "transform", "convert", "create",
    "generate", "lead", "result",
})

OPERATIONAL_PATTERNS = [
    re.compile(r"detected by", re.I),
    re.compile(r"revealed when", re.I),
    re.compile(r"test for", re.I),
    re.compile(r"operationally", re.I),
    re.compile(r"operational test", re.I),
]

COST_PATTERNS = [
    re.compile(r"\brequires?\b", re.I),
    re.compile(r"\bexpends?\b", re.I),
    re.compile(r"\bpays?\b", re.I),
    re.compile(r"\bburden\b", re.I),
    re.compile(r"\bcost\b", re.I),
    re.compile(r"\beffort\b", re.I),
]

SPATIAL_PATTERNS = [
    re.compile(r"\blocal\b", re.I),
    re.compile(r"non-local", re.I),
    re.compile(r"\bboundary\b", re.I),
    re.compile(r"\binside\b", re.I),
    re.compile(r"\bbeyond\b", re.I),
    re.compile(r"\bwithin\b", re.I),
]

# Context-aware prescriptive detection
PRESCRIPTIVE_SUBJECT_PATTERN = re.compile(
    r"\b(we|one|users?|systems?|agents?|operators?)\s+(should|must|require)", re.I
)
DESCRIPTIVE_MODAL_PATTERN = re.compile(
    r"\b(it|this|the\s+\w+)\s+(requires?|must)", re.I
)


# -----------------------------------------------------------------------------
# Phase 1b: Definition Semantic Analysis
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class DefinitionAnalysisItem:
    """Semantic analysis of a single concept definition."""

    name: str
    title: str
    layer: str

    # Verb inventory
    verbs_state: tuple[str, ...] = field(default_factory=tuple)
    verbs_action: tuple[str, ...] = field(default_factory=tuple)
    verbs_modal: tuple[str, ...] = field(default_factory=tuple)
    verbs_causal: tuple[str, ...] = field(default_factory=tuple)

    # Semantic patterns
    negation_count: int = 0
    operational_markers: tuple[str, ...] = field(default_factory=tuple)
    cost_language: tuple[str, ...] = field(default_factory=tuple)
    spatial_metaphors: tuple[str, ...] = field(default_factory=tuple)

    # Implicit dependencies
    implicit_deps: tuple[str, ...] = field(default_factory=tuple)

    # Role purity (context-aware)
    prescriptive_markers: tuple[str, ...] = field(default_factory=tuple)
    role_assessment: str = "descriptive"

    # Definition scope metrics
    definition_sentences: int = 0
    what_not_items: int = 0
    scope_ratio: float = 0.5


def _extract_section(content: str, heading: str) -> str:
    """Extract text from a markdown section (heading to next ## or end)."""
    lowered = content.lower()
    marker = heading.lower()
    idx = lowered.find(marker)
    if idx == -1:
        return ""
    start = idx + len(marker)
    end = lowered.find("\n## ", start)
    if end == -1:
        end = len(content)
    return content[start:end].strip()


def _extract_words(text: str) -> list[str]:
    """Extract lowercase words from text."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def _find_verbs(words: list[str], verb_set: frozenset[str]) -> list[str]:
    """Find all verbs from words that match the verb set."""
    return [w for w in words if w in verb_set]


def _count_negations(text: str) -> int:
    """Count negation patterns in text."""
    patterns = [
        r"\bnot\b",
        r"\bdoes not\b",
        r"\bis not\b",
        r"\bare not\b",
        r"\bdo not\b",
        r"\bcannot\b",
        r"\bwithout\b",
        r"\bnever\b",
    ]
    count = 0
    lowered = text.lower()
    for p in patterns:
        count += len(re.findall(p, lowered))
    return count


def _find_pattern_matches(text: str, patterns: list[re.Pattern]) -> list[str]:
    """Find all matches for a list of patterns."""
    matches = []
    for pat in patterns:
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


def _is_prescriptive_sentence(sentence: str) -> bool:
    """Return True if sentence contains prescriptive language with agentive subject."""
    if PRESCRIPTIVE_SUBJECT_PATTERN.search(sentence):
        return True
    # "X requires Y" without human subject is descriptive
    if DESCRIPTIVE_MODAL_PATTERN.search(sentence):
        return False
    # Check for bare "should" or "must" without clear subject
    if re.search(r"\bshould\b|\bmust\b", sentence, re.I):
        # If no descriptive pattern matched, and no clear prescriptive subject,
        # check if it looks like a general prescription
        if re.search(r"\b(you|we|one)\b", sentence, re.I):
            return True
    return False


def _find_prescriptive_markers(text: str) -> list[str]:
    """Find sentences with prescriptive language."""
    sentences = re.split(r"[.!?]+", text)
    markers = []
    for sent in sentences:
        sent = sent.strip()
        if _is_prescriptive_sentence(sent):
            # Extract the relevant phrase
            match = PRESCRIPTIVE_SUBJECT_PATTERN.search(sent)
            if match:
                markers.append(match.group(0))
            elif re.search(r"\b(you|we|one)\s+(should|must)", sent, re.I):
                m = re.search(r"\b(you|we|one)\s+(should|must)", sent, re.I)
                if m:
                    markers.append(m.group(0))
    return markers


def _calc_scope_metrics(content: str) -> tuple[int, int, float]:
    """Calculate definition scope metrics.

    Returns (definition_sentences, what_not_items, scope_ratio).
    """
    def_section = _extract_section(content, "## Definition")
    not_section = _extract_section(content, "## What this is NOT")

    # Count sentences in definition (by sentence-ending punctuation)
    def_sentences = len(re.findall(r"[.!?]+", def_section))

    # Count "Not X" items (lines starting with "- Not")
    not_items = len(re.findall(r"^-\s+Not\b", not_section, re.M | re.I))

    total = def_sentences + not_items
    ratio = def_sentences / total if total > 0 else 0.5
    return def_sentences, not_items, round(ratio, 2)


def _find_implicit_dependencies(
    content: str,
    declared_deps: list[str],
    all_concept_names: set[str],
    self_name: str,
) -> list[str]:
    """Find concepts mentioned in Definition but not declared as dependencies."""
    def_section = _extract_section(content, "## Definition")
    if not def_section:
        return []

    # Extract linked concepts from Definition section
    linked = set(re.findall(r"\[\[([^\]|]+)", def_section.lower()))

    # Normalize declared deps
    declared_normalized = {d.lower().replace(" ", "-") for d in declared_deps}

    # Normalize self name
    self_normalized = self_name.lower().replace(" ", "-")

    # Find concept names mentioned as plain text but not linked
    implicit = []
    lowered_def = def_section.lower()

    for name in all_concept_names:
        normalized = name.lower().replace(" ", "-")
        # Skip self-references
        if normalized == self_normalized:
            continue
        # Skip if already declared
        if normalized in declared_normalized:
            continue
        # Skip if already linked
        if normalized in linked:
            continue
        # Check if mentioned as plain text (with space or hyphen variants)
        text_variants = [
            name.lower(),
            name.lower().replace("-", " "),
            name.lower().replace(" ", "-"),
        ]
        for variant in text_variants:
            if variant in lowered_def and len(variant) > 3:  # Skip very short matches
                implicit.append(name)
                break

    return implicit


def _analyze_definition(
    graph: DependencyGraph,
    name: str,
    all_concept_names: set[str],
) -> DefinitionAnalysisItem:
    """Analyze a single concept's definition semantics."""
    concept = graph.nodes[name]
    content = concept.content
    def_section = _extract_section(content, "## Definition")

    words = _extract_words(def_section)

    verbs_state = tuple(_find_verbs(words, STATE_VERBS))
    verbs_action = tuple(_find_verbs(words, ACTION_VERBS))
    verbs_modal = tuple(_find_verbs(words, MODAL_VERBS))
    verbs_causal = tuple(_find_verbs(words, CAUSAL_VERBS))

    negation_count = _count_negations(def_section)
    operational_markers = tuple(_find_pattern_matches(def_section, OPERATIONAL_PATTERNS))
    cost_language = tuple(_find_pattern_matches(def_section, COST_PATTERNS))
    spatial_metaphors = tuple(_find_pattern_matches(def_section, SPATIAL_PATTERNS))

    declared_deps = [graph.normalize(d) for d in concept.depends_on]
    implicit_deps = tuple(_find_implicit_dependencies(content, declared_deps, all_concept_names, name))

    prescriptive_markers = tuple(_find_prescriptive_markers(def_section))
    if len(prescriptive_markers) > 2:
        role_assessment = "prescriptive"
    elif len(prescriptive_markers) > 0:
        role_assessment = "mixed"
    else:
        role_assessment = "descriptive"

    def_sentences, what_not_items, scope_ratio = _calc_scope_metrics(content)

    return DefinitionAnalysisItem(
        name=name,
        title=concept.title,
        layer=concept.layer or "unknown",
        verbs_state=verbs_state,
        verbs_action=verbs_action,
        verbs_modal=verbs_modal,
        verbs_causal=verbs_causal,
        negation_count=negation_count,
        operational_markers=operational_markers,
        cost_language=cost_language,
        spatial_metaphors=spatial_metaphors,
        implicit_deps=implicit_deps,
        prescriptive_markers=prescriptive_markers,
        role_assessment=role_assessment,
        definition_sentences=def_sentences,
        what_not_items=what_not_items,
        scope_ratio=scope_ratio,
    )


def run_definition_analysis(
    vault_path: Path,
    *,
    out: Path | None = None,
    top: int = 25,
    fmt: str = "md",
    include_all: bool = False,
) -> int:
    """Generate a definition semantic analysis report (Phase 1b).

    Args:
        vault_path: Path to vault content directory
        out: Optional output file path; prints to stdout if None
        top: Number of top in-degree concepts to analyze (unless include_all)
        fmt: md|json
        include_all: If true, analyze all concepts
    """
    console = Console(stderr=True)

    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
    hub_class_by_concept = _load_hub_classes(vault_path)

    all_concept_names = set(graph.nodes.keys())
    concepts = _select_concepts_for_audit(graph, hub_class_by_concept, top=top, include_all=include_all)
    items = [_analyze_definition(graph, name, all_concept_names) for name in concepts]

    # Compute summary statistics
    high_negation = sum(1 for it in items if it.negation_count >= 5)
    has_operational = sum(1 for it in items if it.operational_markers)
    has_implicit = sum(1 for it in items if it.implicit_deps)
    has_prescriptive = sum(1 for it in items if it.role_assessment != "descriptive")
    high_scope_ratio = sum(1 for it in items if it.scope_ratio > 0.7)
    low_scope_ratio = sum(1 for it in items if it.scope_ratio < 0.3)

    payload = {
        "title": "Definition Semantic Analysis (Phase 1b)",
        "vault": str(vault_path),
        "concept_count": len(graph.nodes),
        "analyzed_count": len(items),
        "summary": {
            "high_negation_density": high_negation,
            "operational_framing": has_operational,
            "implicit_dependencies": has_implicit,
            "prescriptive_language": has_prescriptive,
            "definition_heavy": high_scope_ratio,
            "boundary_primitives": low_scope_ratio,
        },
        "items": [_item_to_dict(it) for it in items],
    }

    if fmt == "json":
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    else:
        text = _definition_analysis_to_markdown(payload)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote definition analysis to {out}", style="green")
    else:
        print(text, end="" if text.endswith("\n") else "\n")

    return 0


def _item_to_dict(item: DefinitionAnalysisItem) -> dict:
    """Convert item to dict for JSON serialization."""
    return {
        "name": item.name,
        "title": item.title,
        "layer": item.layer,
        "verbs_state": list(item.verbs_state),
        "verbs_action": list(item.verbs_action),
        "verbs_modal": list(item.verbs_modal),
        "verbs_causal": list(item.verbs_causal),
        "negation_count": item.negation_count,
        "operational_markers": list(item.operational_markers),
        "cost_language": list(item.cost_language),
        "spatial_metaphors": list(item.spatial_metaphors),
        "implicit_deps": list(item.implicit_deps),
        "prescriptive_markers": list(item.prescriptive_markers),
        "role_assessment": item.role_assessment,
        "definition_sentences": item.definition_sentences,
        "what_not_items": item.what_not_items,
        "scope_ratio": item.scope_ratio,
    }


def _definition_analysis_to_markdown(payload: dict) -> str:
    """Render definition analysis as markdown."""
    items = payload["items"]
    summary = payload["summary"]
    total = payload["analyzed_count"]

    def pct(n: int) -> str:
        return f"{100 * n // total}%" if total > 0 else "0%"

    lines: list[str] = []
    lines.append(f"# {payload['title']}")
    lines.append("")
    lines.append(f"- Vault: `{payload['vault']}`")
    lines.append(f"- Concepts: {payload['concept_count']}")
    lines.append(f"- Analyzed: {total}")
    lines.append("")

    lines.append("## Summary Statistics")
    lines.append("")
    lines.append("| Pattern | Count | % of Analyzed |")
    lines.append("|---------|------:|:-------------:|")
    lines.append(f"| High negation density (5+) | {summary['high_negation_density']} | {pct(summary['high_negation_density'])} |")
    lines.append(f"| Operational framing | {summary['operational_framing']} | {pct(summary['operational_framing'])} |")
    lines.append(f"| Implicit dependencies found | {summary['implicit_dependencies']} | {pct(summary['implicit_dependencies'])} |")
    lines.append(f"| Prescriptive language | {summary['prescriptive_language']} | {pct(summary['prescriptive_language'])} |")
    lines.append(f"| Definition-heavy (ratio >0.7) | {summary['definition_heavy']} | {pct(summary['definition_heavy'])} |")
    lines.append(f"| Boundary primitives (ratio <0.3) | {summary['boundary_primitives']} | {pct(summary['boundary_primitives'])} |")
    lines.append("")

    lines.append("## Per-Concept Analysis")
    lines.append("")

    for it in items:
        lines.append(f"### {it['title']} (`{it['name']}`)")
        lines.append("")
        lines.append(f"- Layer: `{it['layer']}`")
        lines.append(f"- Scope: {it['definition_sentences']} sentences, {it['what_not_items']} NOT items (ratio: {it['scope_ratio']})")
        lines.append("")

        # Verb profile
        lines.append("**Verb profile:**")
        if it["verbs_state"]:
            lines.append(f"- State: {', '.join(it['verbs_state'])}")
        if it["verbs_action"]:
            lines.append(f"- Action: {', '.join(it['verbs_action'])}")
        if it["verbs_modal"]:
            lines.append(f"- Modal: {', '.join(it['verbs_modal'])}")
        if it["verbs_causal"]:
            lines.append(f"- Causal: {', '.join(it['verbs_causal'])}")
        if not any([it["verbs_state"], it["verbs_action"], it["verbs_modal"], it["verbs_causal"]]):
            lines.append("- (none detected)")
        lines.append("")

        # Semantic markers
        lines.append("**Semantic markers:**")
        lines.append(f"- Negation density: {it['negation_count']}" + (" (high)" if it["negation_count"] >= 5 else ""))
        if it["operational_markers"]:
            lines.append(f"- Operational framing: {', '.join(set(it['operational_markers']))}")
        if it["cost_language"]:
            lines.append(f"- Cost language: {', '.join(set(it['cost_language']))}")
        if it["spatial_metaphors"]:
            lines.append(f"- Spatial metaphors: {', '.join(set(it['spatial_metaphors']))}")
        lines.append("")

        # Implicit dependencies
        if it["implicit_deps"]:
            lines.append("**Implicit dependencies:**")
            for dep in it["implicit_deps"]:
                lines.append(f"- `{dep}` mentioned but not linked")
            lines.append("")

        # Role assessment
        lines.append(f"**Role assessment:** {it['role_assessment'].title()}")
        if it["prescriptive_markers"]:
            lines.append(f"- Prescriptive markers: {', '.join(it['prescriptive_markers'])}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# -----------------------------------------------------------------------------
# Phase 1: Concept Audit (original)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ConceptAuditItem:
    name: str
    title: str
    layer: str
    in_degree: int
    out_degree: int
    hub_class: str
    has_definition: bool
    has_structural_dependencies: bool
    has_what_not: bool
    role_purity_flags: list[str]
    deps: list[str]
    deps_only_in_deps_section: list[str]


def run_concept_audit(
    vault_path: Path,
    *,
    out: Path | None = None,
    top: int = 25,
    fmt: str = "md",
    include_all: bool = False,
) -> int:
    """Generate a concept audit report (Phase 1).

    Args:
        vault_path: Path to vault content directory (e.g., ./content)
        out: Optional output file path; prints to stdout if None
        top: Number of top in-degree concepts to include (unless include_all)
        fmt: md|json
        include_all: If true, audit all concepts (not just top list)
    """
    console = Console(stderr=True)

    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
    hub_class_by_concept = _load_hub_classes(vault_path)

    concepts = _select_concepts_for_audit(graph, hub_class_by_concept, top=top, include_all=include_all)
    items = [_audit_concept(graph, name, hub_class_by_concept.get(name, "")) for name in concepts]

    payload = {
        "title": "Concept audit (inside-out)",
        "vault": str(vault_path),
        "top": top,
        "include_all": include_all,
        "concept_count": len(graph.nodes),
        "audited_count": len(items),
        "items": [item.__dict__ for item in items],
    }

    if fmt == "json":
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    else:
        text = _to_markdown(payload)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote concept audit to {out}", style="green")
    else:
        print(text, end="" if text.endswith("\n") else "\n")

    return 0


def _select_concepts_for_audit(
    graph: DependencyGraph,
    hub_class_by_concept: dict[str, str],
    *,
    top: int,
    include_all: bool,
) -> list[str]:
    if include_all:
        return sorted(graph.nodes.keys())

    # Always include hubs.yml concepts, plus top in-degree nodes.
    hub_names = sorted(hub_class_by_concept.keys())

    ranked = sorted(
        graph.nodes.keys(),
        key=lambda n: (len(graph.reverse_edges.get(n, set())), n),
        reverse=True,
    )
    top_names = ranked[: max(0, top)]

    seen: set[str] = set()
    out: list[str] = []
    for name in hub_names + top_names:
        if name not in graph.nodes:
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _audit_concept(graph: DependencyGraph, name: str, hub_class: str) -> ConceptAuditItem:
    concept = graph.nodes[name]
    content = concept.content
    lowered = content.lower()

    has_definition = "\n## definition" in ("\n" + lowered)
    has_structural_deps = "\n## structural dependencies" in ("\n" + lowered)
    has_what_not = "\n## what this is not" in ("\n" + lowered)

    role_purity_flags: list[str] = []
    suspicious_headings = ("## operation", "## procedure", "## checklist", "## how to use", "## steps")
    for h in suspicious_headings:
        if h in lowered:
            role_purity_flags.append(f"Contains operator-like section heading: {h.strip('# ').title()}")
            break
    if "you should" in lowered or "do not" in lowered:
        role_purity_flags.append("Contains prescriptive language (possible operator/policy bleed)")

    deps = [graph.normalize(d) for d in concept.depends_on]
    deps_only_in_deps_section = _deps_only_in_deps_section(content, deps)

    return ConceptAuditItem(
        name=name,
        title=concept.title,
        layer=(concept.layer or "unknown"),
        in_degree=len(graph.reverse_edges.get(name, set())),
        out_degree=len(graph.edges.get(name, set())),
        hub_class=hub_class,
        has_definition=has_definition,
        has_structural_dependencies=has_structural_deps,
        has_what_not=has_what_not,
        role_purity_flags=role_purity_flags,
        deps=deps,
        deps_only_in_deps_section=deps_only_in_deps_section,
    )


def _deps_only_in_deps_section(content: str, deps: list[str]) -> list[str]:
    """Return deps that appear only in the Structural dependencies section."""
    if not deps:
        return []

    # Split into "deps section" and "rest of document" by heading boundaries.
    lowered = content.lower()
    marker = "## structural dependencies"
    idx = lowered.find(marker)
    deps_section = ""
    rest = content
    if idx != -1:
        end = lowered.find("\n## ", idx + len(marker))
        if end == -1:
            end = len(content)
        deps_section = content[idx:end]
        rest = content[:idx] + content[end:]

    only: list[str] = []
    for d in deps:
        needle = f"[[{d}]]".lower()
        in_deps = needle in deps_section.lower()
        in_rest = needle in rest.lower()
        if in_deps and not in_rest:
            only.append(d)
    return only


def _load_hub_classes(vault_path: Path) -> dict[str, str]:
    hubs_path = (vault_path / "meta" / "hubs.yml").resolve()
    if not hubs_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        return {}
    try:
        data = yaml.safe_load(hubs_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

    hubs = data.get("hubs") or {}
    if not isinstance(hubs, dict):
        return {}

    out: dict[str, str] = {}
    for k, v in hubs.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        cls = v.get("class")
        if isinstance(cls, str) and cls.strip():
            out[k.strip().lower()] = cls.strip()
    return out


def _to_markdown(payload: dict) -> str:
    items = [ConceptAuditItem(**d) for d in payload["items"]]

    def yesno(v: bool) -> str:
        return "yes" if v else "no"

    lines: list[str] = []
    lines.append(f"# {payload['title']}")
    lines.append("")
    lines.append(f"- Vault: `{payload['vault']}`")
    lines.append(f"- Concepts: {payload['concept_count']}")
    lines.append(f"- Audited: {payload['audited_count']}")
    lines.append("")
    lines.append("## Top candidates")
    lines.append("")
    lines.append("| Concept | Layer | In-degree | Hub class |")
    lines.append("|---|---:|---:|---|")
    for it in sorted(items, key=lambda x: (x.in_degree, x.name), reverse=True):
        hub = it.hub_class or ""
        lines.append(f"| [[{it.name}]] | {it.layer} | {it.in_degree} | {hub} |")

    lines.append("")
    lines.append("## Audit details")
    lines.append("")
    for it in sorted(items, key=lambda x: (x.in_degree, x.name), reverse=True):
        lines.append(f"### {it.title} (`{it.name}`)")
        lines.append("")
        lines.append(f"- Layer: `{it.layer}`")
        lines.append(f"- In-degree: `{it.in_degree}`  Out-degree: `{it.out_degree}`")
        if it.hub_class:
            lines.append(f"- Hub class: `{it.hub_class}`")
        lines.append(f"- Has `## Definition`: {yesno(it.has_definition)}")
        lines.append(f"- Has `## Structural dependencies`: {yesno(it.has_structural_dependencies)}")
        lines.append(f"- Has `## What this is NOT`: {yesno(it.has_what_not)}")
        if it.role_purity_flags:
            for f in it.role_purity_flags:
                lines.append(f"- Role purity flag: {f}")
        if it.deps:
            lines.append(f"- Declared deps: {', '.join(f'[[{d}]]' for d in it.deps)}")
        if it.deps_only_in_deps_section:
            lines.append(
                "- Dependency fidelity note: these deps appear only in the Structural dependencies section: "
                + ", ".join(f"[[{d}]]" for d in it.deps_only_in_deps_section)
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
