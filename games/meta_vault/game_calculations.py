"""Meta Vault - Custom calculations for ways wins with wild multipliers."""

import random
from src.executables.executables import Executables
from src.calculations.ways import Ways


class GameCalculations(Executables):
    """
    Meta Vault specific calculations.
    Extends base executables with transformation-aware win calculations.
    """
    
    def calculate_win(self):
        """
        Calculate wins for the current board state.
        Applies Meta Vault specific logic:
        1. Wild Multiplier Assignment (Free Games).
        2. Symbol Transformations based on collected 'G' symbols (Free Games).
        3. Standard Ways evaluation.
        4. Scatter Retrigger Logic.
        """
        
        # Initialize persistent data if needed
        if not hasattr(self, 'persistent_data'):
            self.persistent_data = {}

        # 1. Wild Multiplier Assignment (Free Games Only)
        if self.gametype == self.config.freegame_type:
            weights = self.config.wild_multiplier_weights
            choices = list(weights.keys())
            probs = list(weights.values())
            
            for reel in self.board:
                for symbol in reel:
                    if symbol.name == 'W':
                        # Assign W2X or W3X
                        # Use self.rng if available, else random
                        rng = getattr(self, 'rng', random)
                        chosen_wild = rng.choices(choices, weights=probs, k=1)[0]
                        
                        symbol.name = chosen_wild
                        symbol.multiplier = self.config.wild_multiplier_values[chosen_wild]
                        # Add attribute for frontend
                        symbol.add_attribute({'multiplier': symbol.multiplier})

        # 2. Handle Symbol Transformations (Free Games Only)
        if self.gametype == self.config.freegame_type:
            current_g_count = self.persistent_data.get('collector_count', 0)
            
            # Apply Transformations
            transform_map = {}
            if current_g_count >= 13:
                transform_map = {'H4': 'H1', 'H3': 'H1', 'H2': 'H1'}
            elif current_g_count >= 7:
                transform_map = {'H4': 'H1', 'H3': 'H1'}
            elif current_g_count >= 4:
                transform_map = {'H4': 'H1'}
                
            if transform_map:
                for reel in self.board:
                    for symbol in reel:
                        if symbol.name in transform_map:
                            symbol.name = transform_map[symbol.name]
                            symbol.add_attribute({'transformed': True})

        # 3. Standard Ways Calculation
        self.win_data = Ways.get_ways_wins(
            self.config,
            self.board,
            wild_key="wild",
            multiplier_key="multiplier",
            global_multiplier=1
        )
        
        # 4. Apply H1 Multiplier (15+ Gs)
        if self.gametype == self.config.freegame_type:
            current_g_count = self.persistent_data.get('collector_count', 0)
            if current_g_count >= 15:
                for win in self.win_data['wins']:
                    if win['symbol'] == 'H1':
                        win['win'] *= 2
                        win['multiplier'] = win.get('multiplier', 1) * 2
                self.win_data['totalWin'] = sum(w['win'] for w in self.win_data['wins'])

        # 5. Scatter Logic (Trigger/Retrigger)
        scatter_count = 0
        scatter_positions = []
        for r_idx, reel in enumerate(self.board):
            for s_idx, symbol in enumerate(reel):
                if symbol.name == 'S':
                    scatter_count += 1
                    scatter_positions.append({'reel': r_idx, 'row': s_idx})
        
        triggers = self.config.freespin_triggers.get(self.gametype, {})
        if scatter_count in triggers:
            spins_won = triggers[scatter_count]
            # Add scatter win entry
            self.win_data['wins'].append({
                'symbol': 'S',
                'count': scatter_count,
                'positions': scatter_positions,
                'win': 0, # Scatters usually don't pay cash in this math model, just spins
                'freeSpins': spins_won,
                'retrigger': self.gametype == self.config.freegame_type
            })
            # Note: The engine needs to process this 'freeSpins' field to actually award them.

    def update_collection(self):
        """Update the persistent collector count."""
        if self.gametype == self.config.freegame_type:
            if not hasattr(self, 'persistent_data'):
                self.persistent_data = {}
                
            new_gs = 0
            for reel in self.board:
                for symbol in reel:
                    if symbol.name == 'G':
                        new_gs += 1
            
            self.persistent_data['collector_count'] = self.persistent_data.get('collector_count', 0) + new_gs
            
            # Return data for frontend event
            return {
                "collected": new_gs,
                "total": self.persistent_data['collector_count']
            }
        return None

