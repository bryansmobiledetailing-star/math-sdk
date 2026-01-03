"""Meta Vault - Main game state handling base game and free spins."""

from game_override import GameStateOverride


class GameState(GameStateOverride):
    """
    Meta Vault game logic with:
    - Buffalo Gold style gold collection
    - Symbol transformation system
    - Multiplicative wild multipliers
    """

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        """
        Execute a single base game spin.
        May trigger free spins if enough scatters land.
        """
        self.reset_seed(sim)
        self.repeat = True
        
        while self.repeat:
            self.reset_book()
            
            # Draw the base game board
            self.draw_board(emit_event=True)
            
            # Evaluate ways wins on the board
            self.evaluate_ways_board()
            
            # Update wins for this game type
            self.win_manager.update_gametype_wins(self.gametype)
            
            # Check for free spin trigger (3+ scatters)
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()
            
            # Calculate final win and check criteria
            self.evaluate_finalwin()
            self.check_repeat()
        
        self.imprint_wins()

    def run_freespin(self) -> None:
        """
        Execute the free spin bonus round.
        
        KEY MECHANICS:
        1. Gold Vault (G) symbols appear only in free spins
        2. Collecting golds fills the meter
        3. At thresholds (4, 7, 13, 15), high symbols transform to Vault
        4. Wilds get x2 or x3 multipliers that MULTIPLY together
        5. Retriggers add more spins (3S=5, 4S=8, 5S=10)
        """
        # Reset for new free spin session
        self.reset_fs_spin()
        self.reset_fs_session()  # Reset gold collection
        
        while self.fs < self.tot_fs:
            # Update free spin counter
            self.update_freespin()
            
            # Draw board (may contain Gold Vault symbols)
            self.draw_board(emit_event=True)
            
            # ======================================
            # COLLECTOR COLLECTION - The Heart of Meta Vault
            # ======================================
            # Count and collect Collector (C) symbols
            collectors_this_spin = self.process_collector_collection()
            
            # Emit collection event for frontend meter
            # Always emit to keep UI in sync with transformation state
            self.emit_collector_event(collectors_this_spin)
            
            # ======================================
            # SYMBOL TRANSFORMATION (FREE GAMES ONLY)
            # ======================================
            # Apply transformations based on collectors collected
            # This changes H1/H2/H3 to H4 (Access Card) for win calculation
            self.apply_transformations()
            
            # ======================================
            # WIN EVALUATION
            # ======================================
            # Evaluate ways wins on the TRANSFORMED board
            # Wild multipliers stack multiplicatively
            self.evaluate_ways_board()
            
            # Check for retrigger (2+ scatters in free spins - Buffalo style!)
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()
            
            # Update wins for free game
            self.win_manager.update_gametype_wins(self.gametype)
            
            # Check wincap
            if self.get_wincap_triggered():
                break
        
        self.end_freespin()

    def update_fs_retrigger_amt(self, scatter_key: str = "scatter") -> None:
        """
        Override to cap free spins at 125 (Buffalo Gold style).
        
        2+ scatters retrigger in free spins:
        - 2 scatters = +5 spins
        - 3 scatters = +8 spins  
        - 4 scatters = +12 spins
        - 5 scatters = +15 spins
        
        Max 125 total free spins to prevent infinite sessions.
        """
        from src.events.events import fs_trigger_event
        
        scatter_count = self.count_special_symbols(scatter_key)
        spins_to_add = self.config.freespin_triggers[self.gametype].get(scatter_count, 0)
        
        if spins_to_add > 0:
            self.tot_fs += spins_to_add
            
            # Cap at 125 max free spins (Buffalo Gold style)
            if self.tot_fs > self.config.max_freespins:
                self.tot_fs = self.config.max_freespins
            
            fs_trigger_event(self, freegame_trigger=True, basegame_trigger=False)

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """
        Trigger free spins from base game.
        Records the trigger event and initializes the free spin session.
        """
        # Record scatter trigger
        self.record({
            "kind": self.count_special_symbols(scatter_key),
            "symbol": scatter_key,
            "gametype": self.gametype,
        })
        
        # Set initial free spin count
        self.update_freespin_amount()
        
        # Run the free spin bonus
        self.run_freespin()
