"""
Meta Vault Math SDK
97% RTP | 1024-Ways Slot Machine Engine
"""

# This __init__.py is for optional package imports
# The math-sdk is designed to run games directly via `make run GAME=<name>`
# These imports are only available when imported as a package

try:
    from .game_config import (
        Symbol, PAYTABLE, TRANSFORMATION_THRESHOLDS,
        WILD_SYMBOLS, WILD_MULTIPLIERS, TARGET_RTP,
        REEL_COUNT, ROWS_PER_REEL, TOTAL_WAYS,
        get_security_level_color, get_active_transformations
    )

    from .gamestate import GameState, GameEngine, SpinResult, GamePhase, ReelGenerator

    from .game_override import (
        apply_transformations, get_transformation_events,
        calculate_transformation_level, get_infinite_breach_multiplier
    )

    from .ways_evaluator import WaysEvaluator, validate_rtp

    from .books import (
        serialize_event, deserialize_event, EventQueue,
        create_spin_event, create_transformation_event, create_collection_event
    )
except ImportError:
    # Running directly (not as a package) - imports not available
    pass

__version__ = "1.0.0"
__all__ = [
    # Config
    "Symbol", "PAYTABLE", "TRANSFORMATION_THRESHOLDS",
    "WILD_SYMBOLS", "WILD_MULTIPLIERS", "TARGET_RTP",
    "REEL_COUNT", "ROWS_PER_REEL", "TOTAL_WAYS",
    "get_security_level_color", "get_active_transformations",
    
    # Game State
    "GameState", "GameEngine", "SpinResult", "GamePhase", "ReelGenerator",
    
    # Transformations
    "apply_transformations", "get_transformation_events",
    "calculate_transformation_level", "get_infinite_breach_multiplier",
    
    # Evaluator
    "WaysEvaluator", "validate_rtp",
    
    # Serialization
    "serialize_event", "deserialize_event", "EventQueue",
    "create_spin_event", "create_transformation_event", "create_collection_event",
]
