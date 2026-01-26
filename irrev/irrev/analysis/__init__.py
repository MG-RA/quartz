"""
Semantic analysis module for vault content.

This module contains extracted analysis logic from junctions.py,
organized by role:
- semantic_signals: Verb patterns, prescriptive detection, text extraction
"""

from .semantic_signals import (
    # Verb sets
    STATE_VERBS,
    ACTION_VERBS,
    MODAL_VERBS,
    CAUSAL_VERBS,
    # Pattern lists
    OPERATIONAL_PATTERNS,
    COST_PATTERNS,
    SPATIAL_PATTERNS,
    # Regex patterns
    PRESCRIPTIVE_SUBJECT_PATTERN,
    DESCRIPTIVE_MODAL_PATTERN,
    # Functions
    extract_section,
    extract_words,
    find_verbs,
    count_negations,
    find_pattern_matches,
    is_prescriptive_sentence,
    find_prescriptive_markers,
    calc_scope_metrics,
    layer_order_key,
)

__all__ = [
    # Verb sets
    "STATE_VERBS",
    "ACTION_VERBS",
    "MODAL_VERBS",
    "CAUSAL_VERBS",
    # Pattern lists
    "OPERATIONAL_PATTERNS",
    "COST_PATTERNS",
    "SPATIAL_PATTERNS",
    # Regex patterns
    "PRESCRIPTIVE_SUBJECT_PATTERN",
    "DESCRIPTIVE_MODAL_PATTERN",
    # Functions
    "extract_section",
    "extract_words",
    "find_verbs",
    "count_negations",
    "find_pattern_matches",
    "is_prescriptive_sentence",
    "find_prescriptive_markers",
    "calc_scope_metrics",
    "layer_order_key",
]
