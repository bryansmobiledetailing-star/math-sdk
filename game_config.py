"""
Meta Vault Game Configuration
97% RTP | 1024-Ways Slot Machine
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

# Symbol IDs
class Symbol(Enum):
    """Symbol enumeration matching frontend config"""
    # High symbols
    H1 = "H1"  # Architect (cyan hologram) - pays from 2-of-a-kind
    H2 = "H2"  # Encryption (golden cube)
    H3 = "H3"  # Guard Dog
    H4 = "H4"  # Breach (orange circuits)
    
    # Low symbols
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L6 = "L6"
    
    # Special symbols
    W = "W"        # Wild (substitutes for all except Scatter and Collector)
    S = "Scatter"  # Scatter (triggers bonus)
    G = "Collector"  # Collector/Gold Vault (C → G mapping)
    
    # Multiplier wilds
    W2X = "2X"  # 2x Multiplier Wild
    W3X = "3X"  # 3x Multiplier Wild


# 1024-ways configuration: 5 reels x 4 rows = 4^5 = 1024 ways
REEL_COUNT = 5
ROWS_PER_REEL = 4
TOTAL_WAYS = 4 ** REEL_COUNT  # 1024


@dataclass
class PayoutEntry:
    """Defines payout for a symbol match"""
    symbol: Symbol
    min_count: int  # Minimum symbols to trigger payout
    payout_multiplier: float  # Base bet multiplier


# Paytable - 97% RTP tuned
# H1 pays from 2-of-a-kind (special Buffalo Gold mechanic)
PAYTABLE: Dict[Symbol, Dict[int, float]] = {
    # High symbols
    Symbol.H1: {
        2: 1.0,    # H1 pays from 2-of-a-kind
        3: 5.0,
        4: 25.0,
        5: 100.0,
    },
    Symbol.H2: {
        3: 3.0,
        4: 15.0,
        5: 50.0,
    },
    Symbol.H3: {
        3: 2.0,
        4: 10.0,
        5: 40.0,
    },
    Symbol.H4: {
        3: 1.5,
        4: 8.0,
        5: 30.0,
    },
    # Low symbols
    Symbol.L1: {
        3: 1.0,
        4: 5.0,
        5: 20.0,
    },
    Symbol.L2: {
        3: 0.8,
        4: 4.0,
        5: 15.0,
    },
    Symbol.L3: {
        3: 0.6,
        4: 3.0,
        5: 12.0,
    },
    Symbol.L4: {
        3: 0.5,
        4: 2.5,
        5: 10.0,
    },
    Symbol.L6: {
        3: 0.4,
        4: 2.0,
        5: 8.0,
    },
}


# Scatter payouts (trigger free spins)
SCATTER_PAYOUTS = {
    3: 10,  # 10 free spins
    4: 15,  # 15 free spins
    5: 20,  # 20 free spins
}


# Transformation thresholds (Buffalo Gold mechanic)
TRANSFORMATION_THRESHOLDS = {
    4: "H4_TO_H1",   # At 4 collectors, H4 transforms to H1
    7: "H3_TO_H1",   # At 7 collectors, H3 transforms to H1
    13: "H2_TO_H1",  # At 13 collectors, H2 transforms to H1
    15: "INFINITE_BREACH",  # Level 15: 2x multiplier on all H1
}


# Wild configuration
WILD_SYMBOLS = {Symbol.W, Symbol.W2X, Symbol.W3X}
WILD_MULTIPLIERS = {
    Symbol.W: 1,
    Symbol.W2X: 2,
    Symbol.W3X: 3,
}


# Symbols that wilds cannot substitute for
NON_SUBSTITUTABLE = {Symbol.S, Symbol.G}


# RTP Configuration
TARGET_RTP = 0.97  # 97%


# Reel strips (simplified - would be loaded from CSV in production)
# Each reel contains weighted symbol distribution
DEFAULT_REEL_WEIGHTS = {
    Symbol.H1: 2,
    Symbol.H2: 4,
    Symbol.H3: 5,
    Symbol.H4: 6,
    Symbol.L1: 8,
    Symbol.L2: 10,
    Symbol.L3: 12,
    Symbol.L4: 14,
    Symbol.L6: 16,
    Symbol.W: 3,
    Symbol.W2X: 1,
    Symbol.W3X: 1,
    Symbol.S: 2,
    Symbol.G: 3,
}


# Security/Transformation levels for visual states
SECURITY_LEVELS = {
    0: "CYAN",      # Base state
    4: "BLUE",      # First transformation
    7: "PURPLE",    # Second transformation
    13: "RED",      # Third transformation
    15: "INFINITE", # Infinite Breach
}


def get_security_level_color(collector_count: int) -> str:
    """Get the background color based on collector count"""
    color = "CYAN"
    for threshold, level_color in sorted(SECURITY_LEVELS.items()):
        if collector_count >= threshold:
            color = level_color
    return color


def get_active_transformations(collector_count: int) -> List[str]:
    """Get list of active symbol transformations based on collector count"""
    transformations = []
    for threshold, transform in sorted(TRANSFORMATION_THRESHOLDS.items()):
        if collector_count >= threshold:
            transformations.append(transform)
    return transformations
