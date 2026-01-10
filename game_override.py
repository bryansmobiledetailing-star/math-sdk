"""
Meta Vault Game Override / Transformation Logic
Implements Buffalo Gold-style symbol transformations
"""

from typing import List, Tuple, Dict
from copy import deepcopy

from game_config import (
    Symbol, TRANSFORMATION_THRESHOLDS, 
    REEL_COUNT, ROWS_PER_REEL
)


def apply_transformations(
    reels: List[List[Symbol]], 
    collector_count: int
) -> Tuple[List[List[Symbol]], List[str]]:
    """
    Apply symbol transformations based on collector count.
    
    Transformation Logic (Buffalo Gold style):
    - At 4 collectors: H4 → H1
    - At 7 collectors: H3 → H1  
    - At 13 collectors: H2 → H1
    - At 15 collectors (Infinite Breach): 2x multiplier on H1 (handled in evaluator)
    
    Args:
        reels: 5x4 grid of symbols
        collector_count: Current number of collected gold symbols
    
    Returns:
        Tuple of (transformed_reels, list of applied transformations)
    """
    transformed_reels = deepcopy(reels)
    applied_transformations = []
    
    # Build transformation map based on thresholds
    transform_map: Dict[Symbol, Symbol] = {}
    
    # Check each threshold
    if collector_count >= 4:
        transform_map[Symbol.H4] = Symbol.H1
        applied_transformations.append("H4_TO_H1")
    
    if collector_count >= 7:
        transform_map[Symbol.H3] = Symbol.H1
        applied_transformations.append("H3_TO_H1")
    
    if collector_count >= 13:
        transform_map[Symbol.H2] = Symbol.H1
        applied_transformations.append("H2_TO_H1")
    
    if collector_count >= 15:
        applied_transformations.append("INFINITE_BREACH")
    
    # Apply transformations to reels
    for reel_idx in range(REEL_COUNT):
        for row_idx in range(ROWS_PER_REEL):
            current_symbol = transformed_reels[reel_idx][row_idx]
            if current_symbol in transform_map:
                transformed_reels[reel_idx][row_idx] = transform_map[current_symbol]
    
    return transformed_reels, applied_transformations


def get_transformation_events(
    original_reels: List[List[Symbol]],
    transformed_reels: List[List[Symbol]]
) -> List[Dict]:
    """
    Generate transformation events for frontend animation.
    
    Args:
        original_reels: Original symbol grid before transformations
        transformed_reels: Symbol grid after transformations
    
    Returns:
        List of transformation events with position and symbol info
    """
    events = []
    
    for reel_idx in range(REEL_COUNT):
        for row_idx in range(ROWS_PER_REEL):
            original = original_reels[reel_idx][row_idx]
            transformed = transformed_reels[reel_idx][row_idx]
            
            if original != transformed:
                events.append({
                    "type": "symbolTransform",
                    "position": [reel_idx, row_idx],
                    "from": original.value,
                    "to": transformed.value,
                    "animate": True
                })
    
    return events


def calculate_transformation_level(collector_count: int) -> int:
    """
    Calculate the current transformation level (0-4).
    
    Levels:
    - 0: No transformations (0-3 collectors)
    - 1: H4→H1 (4-6 collectors)
    - 2: H3→H1 (7-12 collectors)
    - 3: H2→H1 (13-14 collectors)
    - 4: Infinite Breach (15+ collectors)
    """
    if collector_count >= 15:
        return 4
    elif collector_count >= 13:
        return 3
    elif collector_count >= 7:
        return 2
    elif collector_count >= 4:
        return 1
    return 0


def get_infinite_breach_multiplier(collector_count: int) -> float:
    """
    Get the Infinite Breach multiplier.
    
    At Level 15 (Infinite Breach), all H1 symbols get 2x multiplier.
    """
    if collector_count >= 15:
        return 2.0
    return 1.0


def should_apply_h1_boost(symbol: Symbol, collector_count: int) -> bool:
    """
    Check if a symbol should receive the H1 boost (Infinite Breach).
    """
    return symbol == Symbol.H1 and collector_count >= 15
