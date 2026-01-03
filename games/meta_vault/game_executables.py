"""Meta Vault - Game executables for ways wins with wild multiplier stacking."""

from game_calculations import GameCalculations
from src.calculations.ways import Ways
from src.events.events import win_info_event, set_win_event, set_total_event


class GameExecutables(GameCalculations):
    """
    Meta Vault specific executables.
    Handles ways wins with multiplicative wild multipliers.
    """

    def evaluate_ways_board(self):
        """
        Evaluate ways wins on the current board.
        Uses SDK's built-in ways calculation.
        """
        # Get ways win data - multiplier_strategy="symbol" handles wild multipliers
        self.win_data = Ways.get_ways_data(
            self.config, 
            self.board,
            wild_key="wild",
            global_multiplier=self.global_multiplier,
            multiplier_key="multiplier",
            multiplier_strategy="symbol"
        )
        
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        
        # Emit win events
        self.emit_ways_events()

    def emit_ways_events(self):
        """Emit win events for ways wins."""
        if self.win_manager.spin_win > 0:
            win_info_event(self)
            self.evaluate_wincap()
            set_win_event(self)
        set_total_event(self)

    def emit_collector_event(self, collector_count):
        """
        Emit event for collector collection.
        Frontend uses this to update the collection meter.
        Always emit to keep UI in sync with current state.
        """
        self.book.add_event({
            "type": "collectorCollection",
            "collectorsCollected": collector_count,
            "totalCollectors": self.gold_collected,  # Keep variable name for compatibility
            "transformedSymbols": list(self.transformed_symbols),
        })

    def emit_transformation_event(self, symbol_name):
        """
        Emit event when a symbol transforms.
        Frontend uses this to trigger transformation animation.
        """
        self.book.add_event({
            "type": "symbolTransformation",
            "symbol": symbol_name,
            "transformsTo": "H4",  # All symbols transform to H4 (Access Card)
            "threshold": self.config.transform_thresholds[symbol_name],
            "collectorsCollected": self.gold_collected,
        })
