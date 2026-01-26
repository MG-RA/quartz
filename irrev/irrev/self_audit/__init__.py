"""
Self-audit module for the irrev tool.

This module applies the same invariant detection signals to the tool's own
artifacts (CLI help text, error messages, docstrings) that junctions.py
applies to vault content.

Per Failure Mode #10: "The most serious failure mode is assuming the lens
already accounts for its own limitations."
"""

from .prescriptive_scan import scan_prescriptive_language
from .role_separation import scan_role_separation
from .exemption_detect import scan_exemptions

__all__ = [
    "scan_prescriptive_language",
    "scan_role_separation",
    "scan_exemptions",
]
