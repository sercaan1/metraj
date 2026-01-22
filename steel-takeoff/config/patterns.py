"""
Configuration Patterns
Regex patterns for parsing different annotation formats in construction drawings
"""

import re
from typing import List, Pattern

# Compiled regex patterns for performance

# Pattern: "10ø16" or "10Ø16" - quantity + diameter
QUANTITY_DIAMETER_PATTERN: Pattern = re.compile(
    r'(\d+)\s*[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: "ø12/15" - diameter/spacing
DIAMETER_SPACING_PATTERN: Pattern = re.compile(
    r'[øφ∅ΦƒQ\[]\s*(\d+)\s*/\s*(\d+)',
    re.IGNORECASE
)

# Pattern: "5-ø20" - quantity-diameter with hyphen
QUANTITY_HYPHEN_DIAMETER_PATTERN: Pattern = re.compile(
    r'(\d+)\s*-\s*[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: "ø16" - just diameter
DIAMETER_ONLY_PATTERN: Pattern = re.compile(
    r'[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: "L=800" or "l=800" or "L:800" - length specification
LENGTH_PATTERN: Pattern = re.compile(
    r'[Ll]\s*[=:]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Stirrup notation "etr. ƒ8/15" or "etr.ƒ10/20"
STIRRUP_PATTERN: Pattern = re.compile(
    r'etr\.?\s*[øφ∅ΦƒQ\[]\s*(\d+)\s*/\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Montage notation "mon. 2ƒ12"
MONTAGE_PATTERN: Pattern = re.compile(
    r'mon\.?\s*(\d+)\s*[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Additional bars "ila. 2ƒ14"
ADDITIONAL_PATTERN: Pattern = re.compile(
    r'ila\.?\s*(\d+)\s*[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Body/main bars "gov. 4ƒ16"
BODY_PATTERN: Pattern = re.compile(
    r'gov\.?\s*(\d+)\s*[øφ∅ΦƒQ\[]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Position indicator "(alt)" or "(ust)"
POSITION_INDICATOR_PATTERN: Pattern = re.compile(
    r'\((alt|ust|üst)\)',
    re.IGNORECASE
)

# Pattern: Beam notation like "K101 25X50"
BEAM_NOTATION_PATTERN: Pattern = re.compile(
    r'([KkBb]\d+)\s*(\d+)\s*[Xx]\s*(\d+)',
    re.IGNORECASE
)

# Pattern: Slab notation with distributed reinforcement "ƒ12/20 l=465 (alt)"
SLAB_DISTRIBUTED_PATTERN: Pattern = re.compile(
    r'[øφ∅ΦƒQ\[]\s*(\d+)\s*/\s*(\d+)\s+[Ll]\s*[=:]\s*(\d+)\s*\((alt|ust|üst)\)',
    re.IGNORECASE
)

# Pattern for extracting POZ number from text
POZ_NUMBER_PATTERN: Pattern = re.compile(
    r'(?:poz|POZ|Poz)\.?\s*[:#]?\s*(\d+)',
    re.IGNORECASE
)

# Layer name patterns that indicate rebar content
REBAR_LAYER_PATTERNS: List[Pattern] = [
    re.compile(r'rebar', re.IGNORECASE),
    re.compile(r'steel', re.IGNORECASE),
    re.compile(r'reinforc', re.IGNORECASE),
    re.compile(r'donat[iı]', re.IGNORECASE),  # Turkish: donatı
    re.compile(r'demir', re.IGNORECASE),       # Turkish: demir
    re.compile(r'çelik', re.IGNORECASE),       # Turkish: çelik
    re.compile(r'arm', re.IGNORECASE),         # armature
    re.compile(r'bar', re.IGNORECASE),
    re.compile(r'stirrup', re.IGNORECASE),
    re.compile(r'etriye', re.IGNORECASE),      # Turkish: stirrup
]


def is_rebar_layer(layer_name: str) -> bool:
    """Check if a layer name indicates rebar content"""
    for pattern in REBAR_LAYER_PATTERNS:
        if pattern.search(layer_name):
            return True
    return False
