"""Markdown parsing utilities for wiki-links, sections, and tables."""

import re

# Match [[target]], [[target|display]], [[target#section]], [[target#section|display]]
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def extract_links(content: str) -> list[str]:
    """Extract all wiki-link targets from content.

    Returns normalized (lowercase) link targets, deduplicated.
    """
    matches = WIKILINK_PATTERN.findall(content)
    # Normalize to lowercase and deduplicate while preserving order
    seen = set()
    result = []
    for match in matches:
        normalized = match.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def extract_section(content: str, header: str) -> str | None:
    """Extract content between ## header and next ## or EOF.

    Args:
        content: Markdown content
        header: Section header text (without ##)

    Returns:
        Section content or None if not found
    """
    # Match ## header followed by content until next ## or end
    pattern = rf"^## {re.escape(header)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else None


def extract_structural_dependencies(content: str) -> list[str]:
    """Extract dependencies from '## Structural dependencies' section.

    Handles:
    - "None (primitive)" or similar -> returns empty list
    - List of [[concept]] links -> returns normalized names
    """
    section = extract_section(content, "Structural dependencies")
    if not section:
        return []

    # Check for "None" variants
    lower = section.lower()
    if "none" in lower and ("primitive" in lower or "axiomatic" in lower):
        return []

    return extract_links(section)


def extract_frontmatter_depends_on(frontmatter: dict) -> list[str]:
    """Extract depends_on from frontmatter, handling wiki-link format.

    Frontmatter depends_on can be:
    - List of strings: ["[[Concept#Section]]", "[[Other]]"]
    - Single string with wiki-link
    """
    depends_on = frontmatter.get("depends_on", [])
    if not depends_on:
        return []

    if isinstance(depends_on, str):
        depends_on = [depends_on]

    # Extract link targets from each entry
    result = []
    for entry in depends_on:
        links = extract_links(entry)
        result.extend(links)

    return result


def parse_markdown_table(content: str) -> list[dict[str, str]]:
    """Parse a markdown table into list of dicts.

    Args:
        content: Markdown content containing a table

    Returns:
        List of dicts mapping header -> cell value
    """
    lines = content.strip().split("\n")
    tables = []
    current_table = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            current_table.append(stripped)
        elif current_table:
            # End of table
            if len(current_table) >= 3:  # header, separator, at least one row
                tables.append(_parse_single_table(current_table))
            current_table = []

    # Don't forget last table
    if current_table and len(current_table) >= 3:
        tables.append(_parse_single_table(current_table))

    # Flatten all tables
    result = []
    for table in tables:
        result.extend(table)
    return result


def _parse_single_table(lines: list[str]) -> list[dict[str, str]]:
    """Parse a single markdown table."""
    # Extract headers from first row
    header_line = lines[0]
    headers = [cell.strip() for cell in header_line.split("|")[1:-1]]

    # Skip separator line (lines[1])
    result = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) == len(headers):
            row = dict(zip(headers, cells))
            result.append(row)

    return result
