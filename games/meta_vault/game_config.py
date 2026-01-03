"""Meta Vault game configuration - Symbol transformation and gold collection mechanics."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Meta Vault configuration with transformation thresholds and multiplier wilds."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "meta_vault"
        self.provider_number = 0
        self.working_name = "Meta Vault"
        self.wincap = 50000
        self.win_type = "ways"
        self.rtp = 0.97  # Target 97% RTP
        self.construct_paths()

        # Game Dimensions - 5x4 grid (4 rows per reel)
        self.num_reels = 5
        self.num_rows = [4] * self.num_reels  # 4 rows per reel = 1024 ways

        # ============================================
        # SYMBOL IDs AND PAYTABLE
        # ============================================
        # Symbol Legend:
        # L1-L6: Low symbols (Hex codes: 0x, FF, A1, DE, 7B, 00)
        # H1-H4: High symbols (H4/H3/H2 transform to H1 during free games)
        # W:     WILD (Glitch - Reels 2-4 only, 2x/3x multipliers in FS)
        # S:     SCATTER (Access Key - Free spin trigger)
        # G:     COLLECTOR (Gold/Glitch - Collection symbol, FS only)
        
        self.paytable = {
            # ============================================
            # CYBER VAULT PAYTABLE (Tuned for 97% RTP)
            # ============================================
            # H1 (The Architect/Vault) is the top premium!
            # H4, H3, H2 transform into H1 during free games.
            
            # H1 - The Architect (Main Jackpot Symbol - pays 2-of-a-kind!)
            (5, "H1"): 2.43,
            (4, "H1"): 1.16,
            (3, "H1"): 0.59,
            (2, "H1"): 0.15,    # SIGNATURE: 2-of-a-kind payout!
            
            # H2 - Encryption Core
            (5, "H2"): 1.47,
            (4, "H2"): 0.69,
            (3, "H2"): 0.38,
            
            # H3 - Cyber-Doberman
            (5, "H3"): 1.16,
            (4, "H3"): 0.59,
            (3, "H3"): 0.29,
            
            # H4 - Access Card
            (5, "H4"): 0.69,
            (4, "H4"): 0.29,
            (3, "H4"): 0.14,
            
            # Low Symbols
            (5, "L1"): 0.29,     # 0x
            (4, "L1"): 0.11,
            (3, "L1"): 0.06,
            
            (5, "L2"): 0.23,     # FF
            (4, "L2"): 0.07,
            (3, "L2"): 0.03,
            
            (5, "L3"): 0.23,     # A1
            (4, "L3"): 0.07,
            (3, "L3"): 0.03,
            
            (5, "L4"): 0.14,     # DE
            (4, "L4"): 0.05,
            (3, "L4"): 0.02,
            
            (5, "L5"): 0.14,     # 7B
            (4, "L5"): 0.05,
            (3, "L5"): 0.02,
            
            (5, "L6"): 0.11,     # 00
            (4, "L6"): 0.03,
            (3, "L6"): 0.01,
        }

        self.include_padding = True
        
        # Special symbols configuration
        # W = Wild/Glitch (base game, no multiplier)
        # W2X = Wild with 2x multiplier (free games only)
        # W3X = Wild with 3x multiplier (free games only)
        # S = Scatter/Access Key (triggers free spins)
        # G = Collector/Gold (collection symbol, FS only)
        self.special_symbols = {
            "wild": ["W", "W2X", "W3X"],  # All wild variants
            "scatter": ["S"],
            "multiplier": ["W2X", "W3X"],  # Only 2x/3x carry multipliers
            "collector": ["G"],   # Collector for upgrade feature
        }

        # ============================================
        # TRANSFORMATION THRESHOLDS (FREE GAMES ONLY)
        # ============================================
        # Collectors collected → Symbol transforms to H1 (The Architect)
        # H4, H3, H2 all upgrade to H1 at different thresholds
        self.transform_thresholds = {
            "H4": 4,   # Access Card → H1 at 4 collectors
            "H3": 7,   # Cyber-Doberman → H1 at 7 collectors  
            "H2": 13,  # Encryption Core → H1 at 13 collectors
        }

        # ============================================
        # FREE SPIN TRIGGERS
        # ============================================
        # 2+ scatters retrigger in free spins!
        self.freespin_triggers = {
            self.basegame_type: {3: 8, 4: 15, 5: 20},   # Base game: 3+ scatters to trigger
            self.freegame_type: {2: 5, 3: 8, 4: 12, 5: 15},  # Retrigger: 2+ scatters!
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 1}  # Anticipate from 1 scatter in FS
        
        # Maximum free spins cap
        self.max_freespins = 125

        # ============================================
        # WILD MULTIPLIER SYMBOLS (Free Games Only)
        # ============================================
        # W2X = 2x multiplier wild
        # W3X = 3x multiplier wild
        # Multiple wilds MULTIPLY together (W2X * W3X = x6)
        # Base game uses regular W (no multiplier)
        self.wild_multiplier_values = {
            "W": 1,    # Base wild - no multiplier
            "W2X": 2,  # 2x multiplier wild (free games only)
            "W3X": 3,  # 3x multiplier wild (free games only)
        }
        
        # Weight distribution for 2x vs 3x wilds in free game reels
        self.wild_multiplier_weights = {
            "W2X": 60,   # 60% chance of 2x wild
            "W3X": 40,   # 40% chance of 3x wild
        }
        
        # ============================================
        # CYBER VAULT WIN CONFIGURATION
        # ============================================
        # CRITICAL: Multipliers must be CUMULATIVE_PRODUCT, not additive!
        # x2 × x3 = x6, NOT x2 + x3 = x5
        self.bonus_multiplier_logic = "CUMULATIVE_PRODUCT"
        
        # H1 minimum match set to 2 (signature 2-of-a-kind)
        self.symbol_min_match = {
            "H1": 2,  # The Architect pays from 2 symbols
            "H4": 2,  # Access Card (upgraded) also pays from 2 symbols
            "default": 3,  # All other symbols require 3+
        }
        
        # Win evaluator mode: "ways" for All-Ways-Pay (1024 ways on 5x4)
        self.win_evaluator_mode = "ways"

        # ============================================
        # REEL STRIPS (BUFFALO-STYLE STACKING)
        # ============================================
        # Buffalo-style reels feature:
        # - H1 (Buffalo) appears in contiguous stacks of 3-4
        # - Creates "all-or-nothing" stampede moments
        # - Near-miss teases with walls of Buffaloes
        reels = {
            "BR0": "MetaVault_Base_Final_v2.csv",      # Base game - Buffalo stacked reels
            "FR0": "MetaVault_Free_Final_v2.csv",      # Free spin - Buffalo + Wild stacks
            "FRWCAP": "FRWCAP.csv"               # High-value free spin reels
        }
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        # ============================================
        # BET MODES
        # ============================================
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=0.01,  # ~1% chance to trigger free spins
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 15, 5: 3},
                            "wild_mult_weights": self.wild_multiplier_weights,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.60,  # 60% of spins are losses
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            "wild_mult_weights": {1: 1},  # No multipliers in base
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.39,  # ~39% of spins win in base game
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            "wild_mult_weights": {1: 1},
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 3},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 30, 5: 15},
                            "wild_mult_weights": self.wild_multiplier_weights,
                        },
                    ),
                ],
            ),
        ]

    def read_reels_csv(self, file_path):
        """Read csv from reelstrip path and map numeric IDs to symbol names."""
        reelstrips = super().read_reels_csv(file_path)
        
        # Mapping based on user request
        # 11 -> W (Wild)
        # 12 -> S (Scatter)
        # 13 -> G (Collector)
        symbol_map = {
            "11": "W",
            "12": "S",
            "13": "G"
        }
        
        for reel in reelstrips:
            for i, sym in enumerate(reel):
                if sym in symbol_map:
                    reel[i] = symbol_map[sym]
                    
        return reelstrips
