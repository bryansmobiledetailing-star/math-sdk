"""Meta Vault - Game overrides for symbol transformation and wild multipliers."""

from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """
    Handles Buffalo Gold / Meta Vault specific mechanics:
    - Gold collection during free spins
    - Symbol transformation based on collection thresholds
    - Wild multiplier assignment (x2 or x3) during free spins
    """

    def reset_book(self):
        """Reset game-specific properties at the start of each simulation."""
        super().reset_book()
        # Gold collection tracking - persists across free spin session
        self.gold_collected = 0
        # Track which symbols have been transformed
        self.transformed_symbols = set()
        # Store raw board for frontend animation
        self.raw_board = None

    def reset_fs_session(self):
        """Reset gold collection at the START of a new free spin trigger only."""
        self.gold_collected = 0
        self.transformed_symbols = set()

    def check_freespin_entry(self, scatter_key: str = "scatter") -> bool:
        """
        Override to prevent infinite loops when force_freegame is False.
        Only enforce repeat=True when criteria specifically requires freegame.
        """
        conditions = self.get_current_distribution_conditions()
        
        # If criteria REQUIRES freegame, check if we have enough scatters
        if conditions["force_freegame"]:
            if len(self.special_syms_on_board[scatter_key]) >= min(
                self.config.freespin_triggers[self.gametype].keys()
            ):
                return True
            # Set repeat if we need freegame but didn't trigger it
            self.repeat = True
            return False
        
        # If freegame not required, allow natural entry without forcing repeat
        if len(self.special_syms_on_board[scatter_key]) >= min(
            self.config.freespin_triggers[self.gametype].keys()
        ):
            return True
        return False

    def assign_special_sym_function(self):
        """Define custom functions for special symbols."""
        # W2X and W3X symbols have fixed multipliers based on symbol type
        self.special_symbol_functions = {
            "W": [self.assign_wild_multiplier],
            "W2X": [self.assign_wild_multiplier],
            "W3X": [self.assign_wild_multiplier],
        }

    def assign_wild_multiplier(self, symbol):
        """
        Assign multiplier to wild symbols based on symbol type.
        W = no multiplier (base game only)
        W2X = 2x multiplier (free games only)
        W3X = 3x multiplier (free games only)
        
        CRITICAL: Multiple wilds MULTIPLY together!
        Example: W2X * W3X = x6 total multiplier on the win
        """
        # Get multiplier from config based on symbol name
        multiplier_value = self.config.wild_multiplier_values.get(symbol.name, 1)
        symbol.assign_attribute({"multiplier": multiplier_value})

    def process_collector_collection(self):
        """
        Count Collector symbols (C) on the board and update persistent meter.
        This is THE KEY MECHANIC - Collectors only appear during FREE GAMES.
        
        Collection persists across all spins in a single FS session.
        When thresholds are met, H1/H2/H3 transform to H4.
        """
        collector_count = 0
        for reel in self.board:
            for symbol in reel:
                if symbol.name == "G":
                    collector_count += 1
        
        self.gold_collected += collector_count  # Keep variable name for compatibility
        
        # Check transformation thresholds and transform eligible symbols
        self.check_transformations()
        
        return collector_count

    def check_transformations(self):
        """
        Check if collector count has reached transformation thresholds.
        Transform high symbols to H4 (Access Card) when thresholds are met.
        
        Thresholds (FREE GAMES ONLY):
        - H1 (The Architect) → H4 at 4 collectors
        - H2 (Encryption Core) → H4 at 7 collectors
        - H3 (Cyber-Doberman) → H4 at 10 collectors
        """
        for symbol_name, threshold in self.config.transform_thresholds.items():
            if (self.gold_collected >= threshold and 
                symbol_name not in self.transformed_symbols):
                self.transformed_symbols.add(symbol_name)
                # Record the transformation event
                self.record({
                    "event": "transformation",
                    "symbol": symbol_name,
                    "gold_count": self.gold_collected,
                    "gametype": self.gametype,
                })

    def apply_transformations(self):
        """
        Apply symbol transformations to the current board.
        Creates a transformed board where eligible high symbols become H4 (Access Card).
        
        Returns both raw and transformed boards:
        - Raw board: For frontend animation (shows original symbols)
        - Transformed board: For win calculation (shows H4)
        """
        # Store raw board for animations
        self.raw_board = [[sym for sym in reel] for reel in self.board]
        
        # Apply transformations to the actual board for win calculation
        for reel_idx, reel in enumerate(self.board):
            for row_idx, symbol in enumerate(reel):
                if symbol.name in self.transformed_symbols:
                    # Create H4 (Access Card) symbol to replace the transformed symbol
                    h4_symbol = self.create_symbol("H4")
                    # Preserve any multiplier the original symbol had
                    if symbol.check_attribute("multiplier"):
                        h4_symbol.assign_attribute({
                            "multiplier": symbol.get_attribute("multiplier")
                        })
                    self.board[reel_idx][row_idx] = h4_symbol

    def calculate_wild_multiplier_total(self, winning_positions):
        """
        Calculate total multiplier from all wilds in a win.
        
        CRITICAL: Wild multipliers MULTIPLY together!
        Example: 
        - Wild on Reel 2 with x3
        - Wild on Reel 3 with x2
        - Total multiplier: 3 * 2 = x6
        
        This is what creates those massive Buffalo Gold wins!
        """
        total_multiplier = 1
        
        for pos in winning_positions:
            symbol = self.board[pos["reel"]][pos["row"]]
            if symbol.name == "W" and symbol.check_attribute("multiplier"):
                mult = symbol.get_attribute("multiplier")
                if mult > 1:
                    total_multiplier *= mult
        
        return total_multiplier

    def check_game_repeat(self):
        """Verify final simulation outcomes satisfied all distribution/criteria conditions."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not self.triggered_freegame:
                self.repeat = True

        self.repeat_count += 1
        self.check_current_repeat_count()
