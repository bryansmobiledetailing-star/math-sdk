"""
Meta Vault 1024-Ways Evaluator
Implements ways-to-win evaluation with multiplicative wild multipliers
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from game_config import (
    Symbol, PAYTABLE, WILD_SYMBOLS, WILD_MULTIPLIERS, 
    NON_SUBSTITUTABLE, REEL_COUNT, ROWS_PER_REEL
)


class WaysEvaluator:
    """
    Evaluates wins using the 1024-ways mechanic.
    
    Ways Mechanic:
    - Match symbols left-to-right starting from reel 1
    - Each reel position that matches continues the way
    - Total ways = product of matching positions per reel
    - Wilds substitute for all symbols (except Scatter and Collector)
    - Wild multipliers are MULTIPLICATIVE (2x × 3x = 6x, not 5x)
    """
    
    def __init__(self, reels: List[List[Symbol]], bet: float):
        """
        Initialize evaluator with reel result and bet amount.
        
        Args:
            reels: 5x4 grid of symbols (list of 5 reels, each with 4 symbols)
            bet: Bet amount for payout calculation
        """
        self.reels = reels
        self.bet = bet
        self.wins: List[Dict[str, Any]] = []
    
    def evaluate(self) -> List[Dict[str, Any]]:
        """
        Evaluate all ways wins.
        
        Returns:
            List of win dictionaries with symbol, count, ways, payout, etc.
        """
        self.wins = []
        
        # Get all unique non-wild, non-scatter symbols to evaluate
        symbols_to_check = self._get_payable_symbols()
        
        for symbol in symbols_to_check:
            win = self._evaluate_symbol(symbol)
            if win:
                self.wins.append(win)
        
        return self.wins
    
    def _get_payable_symbols(self) -> Set[Symbol]:
        """Get all payable symbols from the paytable"""
        return set(PAYTABLE.keys())
    
    def _evaluate_symbol(self, target_symbol: Symbol) -> Optional[Dict[str, Any]]:
        """
        Evaluate wins for a specific symbol.
        
        Args:
            target_symbol: The symbol to evaluate
        
        Returns:
            Win dictionary if win found, None otherwise
        """
        # Track matching positions and multipliers per reel
        reel_matches: List[List[Tuple[int, int]]] = []  # [(row_idx, multiplier), ...]
        
        for reel_idx in range(REEL_COUNT):
            matches = []
            for row_idx in range(ROWS_PER_REEL):
                symbol = self.reels[reel_idx][row_idx]
                
                # Check for exact match
                if symbol == target_symbol:
                    matches.append((row_idx, 1))
                # Check for wild substitution
                elif symbol in WILD_SYMBOLS and target_symbol not in NON_SUBSTITUTABLE:
                    multiplier = WILD_MULTIPLIERS.get(symbol, 1)
                    matches.append((row_idx, multiplier))
            
            if not matches:
                # No matches on this reel - way ends here
                break
            
            reel_matches.append(matches)
        
        # Calculate win if we have enough matching reels
        match_count = len(reel_matches)
        
        # Special case: H1 pays from 2-of-a-kind
        min_match = 2 if target_symbol == Symbol.H1 else 3
        
        if match_count < min_match:
            return None
        
        # Get payout from paytable
        symbol_payouts = PAYTABLE.get(target_symbol)
        if not symbol_payouts or match_count not in symbol_payouts:
            return None
        
        base_payout = symbol_payouts[match_count]
        
        # Calculate ways and multiplicative multiplier
        ways, total_multiplier = self._calculate_ways_and_multiplier(reel_matches)
        
        # Final payout: base_payout × bet × ways × multiplier
        final_payout = base_payout * self.bet * ways * total_multiplier
        
        # Get all winning positions
        positions = self._get_winning_positions(reel_matches)
        
        return {
            "symbol": target_symbol,
            "count": match_count,
            "ways": ways,
            "multiplier": total_multiplier,
            "base_payout": base_payout,
            "payout": final_payout,
            "positions": positions
        }
    
    def _calculate_ways_and_multiplier(
        self, 
        reel_matches: List[List[Tuple[int, int]]]
    ) -> Tuple[int, float]:
        """
        Calculate total ways and multiplicative multiplier.
        
        For each way, multipliers from all wilds in that way are multiplied together.
        The total multiplier is the sum of all way multipliers.
        
        Example: 
        - Reel 1: [H1(1x), W2X(2x)]
        - Reel 2: [H1(1x)]
        - Reel 3: [W3X(3x)]
        
        Ways: 2 × 1 × 1 = 2 ways
        Way 1 (H1-H1-W3X): 1 × 1 × 3 = 3x
        Way 2 (W2X-H1-W3X): 2 × 1 × 3 = 6x
        Total effective multiplier: (3 + 6) / 2 = 4.5x average
        
        For simplicity, we calculate total_ways and average_multiplier.
        """
        if not reel_matches:
            return 0, 1.0
        
        # Calculate total ways
        ways = 1
        for matches in reel_matches:
            ways *= len(matches)
        
        # Calculate sum of all way multipliers using recursive enumeration
        total_multiplier_sum = self._enumerate_way_multipliers(reel_matches, 0, 1.0)
        
        # Return ways and average multiplier
        # (We multiply by ways in the payout calc, so average is what we need)
        avg_multiplier = total_multiplier_sum / ways if ways > 0 else 1.0
        
        return ways, avg_multiplier
    
    def _enumerate_way_multipliers(
        self, 
        reel_matches: List[List[Tuple[int, int]]], 
        reel_idx: int, 
        current_multiplier: float
    ) -> float:
        """
        Recursively enumerate all ways and sum their multipliers.
        
        This implements MULTIPLICATIVE wild multipliers:
        If a way passes through W2X and W3X, the multiplier is 2×3=6x, not 2+3=5x.
        """
        if reel_idx >= len(reel_matches):
            return current_multiplier
        
        total = 0.0
        for row_idx, multiplier in reel_matches[reel_idx]:
            # Multiply current multiplier with this position's multiplier
            new_multiplier = current_multiplier * multiplier
            total += self._enumerate_way_multipliers(
                reel_matches, reel_idx + 1, new_multiplier
            )
        
        return total
    
    def _get_winning_positions(
        self, 
        reel_matches: List[List[Tuple[int, int]]]
    ) -> List[Tuple[int, int]]:
        """Get all positions involved in the win"""
        positions = []
        for reel_idx, matches in enumerate(reel_matches):
            for row_idx, _ in matches:
                positions.append((reel_idx, row_idx))
        return positions


def validate_rtp(num_simulations: int = 100000, bet: float = 1.0) -> Dict[str, float]:
    """
    Validate RTP through simulation.
    
    Args:
        num_simulations: Number of spins to simulate
        bet: Bet amount per spin
    
    Returns:
        Dictionary with RTP statistics
    """
    from gamestate import ReelGenerator
    
    generator = ReelGenerator()
    total_wagered = 0.0
    total_won = 0.0
    hit_count = 0
    
    for _ in range(num_simulations):
        reels = generator.generate_spin()
        evaluator = WaysEvaluator(reels, bet)
        wins = evaluator.evaluate()
        
        total_wagered += bet
        spin_win = sum(w["payout"] for w in wins)
        total_won += spin_win
        
        if spin_win > 0:
            hit_count += 1
    
    rtp = total_won / total_wagered if total_wagered > 0 else 0
    hit_rate = hit_count / num_simulations if num_simulations > 0 else 0
    
    return {
        "rtp": rtp,
        "hit_rate": hit_rate,
        "total_wagered": total_wagered,
        "total_won": total_won,
        "simulations": num_simulations
    }
