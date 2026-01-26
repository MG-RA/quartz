"""
Semantic signal detection for vault content.

This module provides verb patterns, prescriptive language detection,
and text extraction utilities used by the junctions analysis commands.

All functions are pure (stateless) and operate on text input.
"""

from __future__ import annotations

import re


# -----------------------------------------------------------------------------
# Verb inventories
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


# -----------------------------------------------------------------------------
# Semantic pattern lists
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Prescriptive detection patterns
# -----------------------------------------------------------------------------

# Context-aware prescriptive detection
PRESCRIPTIVE_SUBJECT_PATTERN = re.compile(
    r"\b(we|one|users?|systems?|agents?|operators?)\s+(should|must|require)", re.I
)
DESCRIPTIVE_MODAL_PATTERN = re.compile(
    r"\b(it|this|the\s+\w+)\s+(requires?|must)", re.I
)


# -----------------------------------------------------------------------------
# Text extraction utilities
# -----------------------------------------------------------------------------

def extract_section(content: str, heading: str) -> str:
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


def extract_words(text: str) -> list[str]:
    """Extract lowercase words from text."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def find_verbs(words: list[str], verb_set: frozenset[str]) -> list[str]:
    """Find all verbs from words that match the verb set."""
    return [w for w in words if w in verb_set]


def count_negations(text: str) -> int:
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


def find_pattern_matches(text: str, patterns: list[re.Pattern]) -> list[str]:
    """Find all matches for a list of patterns."""
    matches = []
    for pat in patterns:
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


# -----------------------------------------------------------------------------
# Prescriptive language detection
# -----------------------------------------------------------------------------

def is_prescriptive_sentence(sentence: str) -> bool:
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


def find_prescriptive_markers(text: str) -> list[str]:
    """Find sentences with prescriptive language."""
    sentences = re.split(r"[.!?]+", text)
    markers = []
    for sent in sentences:
        sent = sent.strip()
        if is_prescriptive_sentence(sent):
            # Extract the relevant phrase
            match = PRESCRIPTIVE_SUBJECT_PATTERN.search(sent)
            if match:
                markers.append(match.group(0))
            elif re.search(r"\b(you|we|one)\s+(should|must)", sent, re.I):
                m = re.search(r"\b(you|we|one)\s+(should|must)", sent, re.I)
                if m:
                    markers.append(m.group(0))
    return markers


# -----------------------------------------------------------------------------
# Scope metrics
# -----------------------------------------------------------------------------

def calc_scope_metrics(content: str) -> tuple[int, int, float]:
    """Calculate definition scope metrics.

    Returns (definition_sentences, what_not_items, scope_ratio).
    """
    def_section = extract_section(content, "## Definition")
    not_section = extract_section(content, "## What this is NOT")

    # Count sentences in definition (by sentence-ending punctuation)
    def_sentences = len(re.findall(r"[.!?]+", def_section))

    # Count "Not X" items (lines starting with "- Not")
    not_items = len(re.findall(r"^-\s+Not\b", not_section, re.M | re.I))

    total = def_sentences + not_items
    ratio = def_sentences / total if total > 0 else 0.5
    return def_sentences, not_items, round(ratio, 2)


# -----------------------------------------------------------------------------
# Layer ordering
# -----------------------------------------------------------------------------

LAYER_ORDER = {
    "primitive": 0,
    "foundational": 0,
    "first-order": 1,
    "mechanism": 2,
    "accounting": 3,
    "selector": 4,
    "failure-state": 4,
    "meta-analytical": 4,
}


def layer_order_key(layer: str) -> int:
    """Return sort key for layer (lower = more primitive)."""
    return LAYER_ORDER.get(layer.lower(), 99)
