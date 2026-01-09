"""
Meta Vault Game State Management
Handles game rounds, transformations, and event emission
"""

import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from game_config import (
    Symbol, REEL_COUNT, ROWS_PER_REEL, 
    TRANSFORMATION_THRESHOLDS, WILD_SYMBOLS, NON_SUBSTITUTABLE,
    get_security_level_color, get_active_transformations, DEFAULT_REEL_WEIGHTS
)


class GamePhase(Enum):
    """Current phase of the game"""
    IDLE = "idle"
    SPINNING = "spinning"
    REVEALING = "revealing"
    EVALUATING = "evaluating"
    PAYING = "paying"


@dataclass
class SpinResult:
    """Result of a single spin"""
    reels: List[List[Symbol]]  # 5 reels x 4 rows
    original_reels: List[List[Symbol]]  # Before transformations
    wins: List[Dict[str, Any]]
    total_win: float
    multiplier: float
    collector_count: int
    transformations_applied: List[str]
    events: List[Dict[str, Any]]


@dataclass
class GameState:
    """Maintains the current state of the game"""
    collector_count: int = 0
    current_bet: float = 1.0
    balance: float = 1000.0
    phase: GamePhase = GamePhase.IDLE
    free_spins_remaining: int = 0
    transformation_level: int = 0
    infinite_breach_active: bool = False
    session_id: str = ""
    
    # Event queue for frontend synchronization
    pending_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event for frontend consumption"""
        self.pending_events.append({
            "type": event_type,
            "data": data,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        import time
        return int(time.time() * 1000)
    
    def flush_events(self) -> List[Dict[str, Any]]:
        """Get and clear pending events"""
        events = self.pending_events.copy()
        self.pending_events = []
        return events
    
    def update_transformation_level(self) -> List[str]:
        """Update transformation level based on collector count"""
        new_transformations = []
        
        for threshold, transform in sorted(TRANSFORMATION_THRESHOLDS.items()):
            if self.collector_count >= threshold:
                if threshold > self.transformation_level:
                    # New transformation unlocked
                    new_transformations.append(transform)
                    self.emit_event("symbolTransformation", {
                        "threshold": threshold,
                        "transformation": transform,
                        "collectorCount": self.collector_count
                    })
                    
                    if transform == "INFINITE_BREACH":
                        self.infinite_breach_active = True
                        self.emit_event("infiniteBreach", {
                            "active": True,
                            "multiplier": 2
                        })
        
        # Update level to highest achieved threshold
        for threshold in sorted(TRANSFORMATION_THRESHOLDS.keys(), reverse=True):
            if self.collector_count >= threshold:
                self.transformation_level = threshold
                break
        
        return new_transformations
    
    def add_collectors(self, count: int) -> None:
        """Add collectors and emit collection event"""
        old_count = self.collector_count
        self.collector_count += count
        
        self.emit_event("collectorCollection", {
            "previousCount": old_count,
            "newCount": self.collector_count,
            "collected": count
        })
        
        # Check for new transformations
        self.update_transformation_level()
    
    def get_security_color(self) -> str:
        """Get current security level color"""
        return get_security_level_color(self.collector_count)


class ReelGenerator:
    """Generates reel outcomes based on weighted probabilities"""
    
    def __init__(self, reel_weights: Optional[Dict[Symbol, int]] = None):
        self.reel_weights = reel_weights or DEFAULT_REEL_WEIGHTS
        self._build_weighted_list()
    
    def _build_weighted_list(self) -> None:
        """Build weighted symbol list for random selection"""
        self.weighted_symbols = []
        for symbol, weight in self.reel_weights.items():
            self.weighted_symbols.extend([symbol] * weight)
    
    def generate_spin(self) -> List[List[Symbol]]:
        """Generate a random spin result (5 reels x 4 rows)"""
        reels = []
        for _ in range(REEL_COUNT):
            reel = []
            for _ in range(ROWS_PER_REEL):
                symbol = random.choice(self.weighted_symbols)
                reel.append(symbol)
            reels.append(reel)
        return reels


class GameEngine:
    """Main game engine orchestrating spins and evaluations"""
    
    def __init__(self, state: Optional[GameState] = None):
        self.state = state or GameState()
        self.reel_generator = ReelGenerator()
    
    def spin(self, bet: float) -> SpinResult:
        """Execute a spin with the given bet"""
        from ways_evaluator import WaysEvaluator
        from game_override import apply_transformations
        
        if bet > self.state.balance:
            raise ValueError("Insufficient balance")
        
        # Deduct bet
        self.state.balance -= bet
        self.state.current_bet = bet
        self.state.phase = GamePhase.SPINNING
        
        # Generate reels
        original_reels = self.reel_generator.generate_spin()
        
        # Count collectors in this spin
        collectors_in_spin = sum(
            1 for reel in original_reels 
            for sym in reel 
            if sym == Symbol.G
        )
        
        if collectors_in_spin > 0:
            self.state.add_collectors(collectors_in_spin)
        
        # Apply transformations based on collector count
        transformed_reels, transformations_applied = apply_transformations(
            original_reels, 
            self.state.collector_count
        )
        
        self.state.phase = GamePhase.EVALUATING
        
        # Evaluate wins
        evaluator = WaysEvaluator(transformed_reels, bet)
        wins = evaluator.evaluate()
        
        # Apply Infinite Breach multiplier if active
        multiplier = 1.0
        if self.state.infinite_breach_active:
            multiplier = 2.0
            for win in wins:
                if win["symbol"] == Symbol.H1:
                    win["payout"] *= 2
        
        total_win = sum(win["payout"] for win in wins)
        
        # Emit reveal event for screen shake check
        h1_stacks = self._count_h1_stacks(transformed_reels)
        if h1_stacks >= 3:
            self.state.emit_event("reveal", {
                "h1StackCount": h1_stacks,
                "triggerScreenShake": True
            })
        
        # Emit win events
        if wins:
            winning_positions = self._get_winning_positions(wins)
            self.state.emit_event("win", {
                "totalWin": total_win,
                "wins": [self._serialize_win(w) for w in wins],
                "winningPositions": winning_positions,
                "nonWinningDimmed": True
            })
        
        self.state.phase = GamePhase.PAYING
        self.state.balance += total_win
        
        result = SpinResult(
            reels=transformed_reels,
            original_reels=original_reels,
            wins=wins,
            total_win=total_win,
            multiplier=multiplier,
            collector_count=self.state.collector_count,
            transformations_applied=transformations_applied,
            events=self.state.flush_events()
        )
        
        self.state.phase = GamePhase.IDLE
        return result
    
    def _count_h1_stacks(self, reels: List[List[Symbol]]) -> int:
        """Count stacks of 3+ H1 symbols on any reel"""
        stacks = 0
        for reel in reels:
            h1_count = sum(1 for sym in reel if sym == Symbol.H1)
            if h1_count >= 3:
                stacks += 1
        return stacks
    
    def _get_winning_positions(self, wins: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
        """Extract all winning positions from wins"""
        positions = set()
        for win in wins:
            for pos in win.get("positions", []):
                positions.add(tuple(pos))
        return list(positions)
    
    def _serialize_win(self, win: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize win for JSON output"""
        return {
            "symbol": win["symbol"].value if isinstance(win["symbol"], Symbol) else win["symbol"],
            "count": win["count"],
            "payout": win["payout"],
            "ways": win["ways"],
            "multiplier": win.get("multiplier", 1)
        }
