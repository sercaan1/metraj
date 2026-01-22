"""
Domain Constants
Standard rebar specifications and unit weights
"""

from typing import Dict

# Standard rebar diameters (mm)
STANDARD_DIAMETERS: tuple = (6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40)

# Unit weights kg/m for standard rebar diameters (calculated from π * d² / 4 * 7850 kg/m³)
UNIT_WEIGHTS: Dict[int, float] = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.208,
    16: 1.578,
    18: 1.998,
    20: 2.466,
    22: 2.984,
    25: 3.853,
    28: 4.834,
    32: 6.313,
    36: 7.990,
    40: 9.864,
}

# Rebar shape types
class RebarShape:
    STRAIGHT = "STRAIGHT"
    L_SHAPE = "L-SHAPE"
    U_SHAPE = "U-SHAPE"
    STIRRUP = "STIRRUP"
    CLOSED = "CLOSED"
    BENT = "BENT"
    UNKNOWN = "UNKNOWN"


# Rebar types (Turkish construction terminology)
class RebarType:
    MAIN = "MAIN"           # Ana donatı / Govde
    STIRRUP = "STIRRUP"     # Etriye
    MONTAGE = "MONTAGE"     # Montaj demiri
    ADDITIONAL = "ADDITIONAL"  # İlave donatı
    TOP = "TOP"             # Üst donatı
    BOTTOM = "BOTTOM"       # Alt donatı
    DISTRIBUTED = "DISTRIBUTED"  # Yayılı donatı


# Turkish keyword mappings
TURKISH_KEYWORDS: Dict[str, str] = {
    'etr': RebarType.STIRRUP,
    'etr.': RebarType.STIRRUP,
    'etriye': RebarType.STIRRUP,
    'mon': RebarType.MONTAGE,
    'mon.': RebarType.MONTAGE,
    'montaj': RebarType.MONTAGE,
    'ila': RebarType.ADDITIONAL,
    'ila.': RebarType.ADDITIONAL,
    'ilave': RebarType.ADDITIONAL,
    'gov': RebarType.MAIN,
    'gov.': RebarType.MAIN,
    'govde': RebarType.MAIN,
    'gövde': RebarType.MAIN,
    'alt': RebarType.BOTTOM,
    '(alt)': RebarType.BOTTOM,
    'ust': RebarType.TOP,
    'üst': RebarType.TOP,
    '(ust)': RebarType.TOP,
    '(üst)': RebarType.TOP,
}

# Diameter symbol variations found in Turkish drawings
DIAMETER_SYMBOLS: tuple = ('ø', 'φ', '∅', 'Φ', 'ƒ', '[', 'Q', 'q')
