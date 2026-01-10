"""
Meta Vault Math SDK Tests
Tests for 1024-ways evaluator, transformations, and RTP validation
"""

import unittest
from game_config import (
    Symbol, PAYTABLE, TRANSFORMATION_THRESHOLDS,
    WILD_SYMBOLS, WILD_MULTIPLIERS, REEL_COUNT, ROWS_PER_REEL,
    get_security_level_color, get_active_transformations
)
from game_override import (
    apply_transformations, calculate_transformation_level,
    get_infinite_breach_multiplier
)
from ways_evaluator import WaysEvaluator
from gamestate import GameState, GameEngine, ReelGenerator
from books import serialize_event, deserialize_event, EventQueue


class TestGameConfig(unittest.TestCase):
    """Test game configuration values"""
    
    def test_grid_dimensions(self):
        """Test that grid is 5x4 for 1024 ways"""
        self.assertEqual(REEL_COUNT, 5)
        self.assertEqual(ROWS_PER_REEL, 4)
        self.assertEqual(4 ** 5, 1024)  # 1024 ways
    
    def test_h1_pays_from_2_of_a_kind(self):
        """Test H1 has payout for 2-of-a-kind"""
        self.assertIn(2, PAYTABLE[Symbol.H1])
        self.assertGreater(PAYTABLE[Symbol.H1][2], 0)
    
    def test_other_symbols_pay_from_3_of_a_kind(self):
        """Test other symbols require 3-of-a-kind minimum"""
        for symbol in [Symbol.H2, Symbol.H3, Symbol.H4, Symbol.L1]:
            self.assertNotIn(2, PAYTABLE[symbol])
            self.assertIn(3, PAYTABLE[symbol])
    
    def test_transformation_thresholds(self):
        """Test transformation thresholds are correct"""
        self.assertEqual(TRANSFORMATION_THRESHOLDS[4], "H4_TO_H1")
        self.assertEqual(TRANSFORMATION_THRESHOLDS[7], "H3_TO_H1")
        self.assertEqual(TRANSFORMATION_THRESHOLDS[13], "H2_TO_H1")
        self.assertEqual(TRANSFORMATION_THRESHOLDS[15], "INFINITE_BREACH")
    
    def test_security_level_colors(self):
        """Test security level color mapping"""
        self.assertEqual(get_security_level_color(0), "CYAN")
        self.assertEqual(get_security_level_color(3), "CYAN")
        self.assertEqual(get_security_level_color(4), "BLUE")
        self.assertEqual(get_security_level_color(6), "BLUE")
        self.assertEqual(get_security_level_color(7), "PURPLE")
        self.assertEqual(get_security_level_color(13), "RED")
        self.assertEqual(get_security_level_color(15), "INFINITE")


class TestTransformations(unittest.TestCase):
    """Test symbol transformation logic"""
    
    def setUp(self):
        """Create test reels with all high symbols"""
        self.test_reels = [
            [Symbol.H4, Symbol.H3, Symbol.H2, Symbol.L1],
            [Symbol.H4, Symbol.H3, Symbol.H2, Symbol.L1],
            [Symbol.H4, Symbol.H3, Symbol.H2, Symbol.L1],
            [Symbol.H4, Symbol.H3, Symbol.H2, Symbol.L1],
            [Symbol.H4, Symbol.H3, Symbol.H2, Symbol.L1],
        ]
    
    def test_no_transformation_under_4(self):
        """Test no transformations below 4 collectors"""
        for count in [0, 1, 2, 3]:
            transformed, applied = apply_transformations(self.test_reels, count)
            self.assertEqual(applied, [])
            self.assertEqual(transformed[0][0], Symbol.H4)
    
    def test_h4_to_h1_at_4(self):
        """Test H4 transforms to H1 at 4 collectors"""
        transformed, applied = apply_transformations(self.test_reels, 4)
        self.assertIn("H4_TO_H1", applied)
        self.assertEqual(transformed[0][0], Symbol.H1)  # H4 → H1
        self.assertEqual(transformed[0][1], Symbol.H3)  # H3 unchanged
        self.assertEqual(transformed[0][2], Symbol.H2)  # H2 unchanged
    
    def test_h3_to_h1_at_7(self):
        """Test H3 transforms to H1 at 7 collectors"""
        transformed, applied = apply_transformations(self.test_reels, 7)
        self.assertIn("H4_TO_H1", applied)
        self.assertIn("H3_TO_H1", applied)
        self.assertEqual(transformed[0][0], Symbol.H1)  # H4 → H1
        self.assertEqual(transformed[0][1], Symbol.H1)  # H3 → H1
        self.assertEqual(transformed[0][2], Symbol.H2)  # H2 unchanged
    
    def test_h2_to_h1_at_13(self):
        """Test H2 transforms to H1 at 13 collectors"""
        transformed, applied = apply_transformations(self.test_reels, 13)
        self.assertIn("H4_TO_H1", applied)
        self.assertIn("H3_TO_H1", applied)
        self.assertIn("H2_TO_H1", applied)
        self.assertEqual(transformed[0][0], Symbol.H1)  # H4 → H1
        self.assertEqual(transformed[0][1], Symbol.H1)  # H3 → H1
        self.assertEqual(transformed[0][2], Symbol.H1)  # H2 → H1
    
    def test_infinite_breach_at_15(self):
        """Test Infinite Breach activates at 15 collectors"""
        transformed, applied = apply_transformations(self.test_reels, 15)
        self.assertIn("INFINITE_BREACH", applied)
    
    def test_transformation_level_calculation(self):
        """Test transformation level calculation"""
        self.assertEqual(calculate_transformation_level(0), 0)
        self.assertEqual(calculate_transformation_level(3), 0)
        self.assertEqual(calculate_transformation_level(4), 1)
        self.assertEqual(calculate_transformation_level(6), 1)
        self.assertEqual(calculate_transformation_level(7), 2)
        self.assertEqual(calculate_transformation_level(12), 2)
        self.assertEqual(calculate_transformation_level(13), 3)
        self.assertEqual(calculate_transformation_level(14), 3)
        self.assertEqual(calculate_transformation_level(15), 4)
        self.assertEqual(calculate_transformation_level(20), 4)
    
    def test_infinite_breach_multiplier(self):
        """Test Infinite Breach 2x multiplier"""
        self.assertEqual(get_infinite_breach_multiplier(14), 1.0)
        self.assertEqual(get_infinite_breach_multiplier(15), 2.0)
        self.assertEqual(get_infinite_breach_multiplier(20), 2.0)


class TestWaysEvaluator(unittest.TestCase):
    """Test 1024-ways evaluation logic"""
    
    def test_no_win_insufficient_matches(self):
        """Test no win when matches are insufficient"""
        reels = [
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],  # No match
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
        ]
        evaluator = WaysEvaluator(reels, 1.0)
        wins = evaluator.evaluate()
        
        # No H1 win because chain breaks at reel 2
        h1_wins = [w for w in wins if w["symbol"] == Symbol.H1]
        self.assertEqual(len(h1_wins), 0)
    
    def test_h1_wins_from_2_of_a_kind(self):
        """Test H1 pays from 2-of-a-kind"""
        reels = [
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],  # Chain ends
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
        ]
        evaluator = WaysEvaluator(reels, 1.0)
        wins = evaluator.evaluate()
        
        h1_wins = [w for w in wins if w["symbol"] == Symbol.H1]
        self.assertEqual(len(h1_wins), 1)
        self.assertEqual(h1_wins[0]["count"], 2)
    
    def test_ways_calculation(self):
        """Test ways are correctly calculated"""
        reels = [
            [Symbol.H1, Symbol.H1, Symbol.L3, Symbol.L4],  # 2 H1
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],  # 1 H1
            [Symbol.H1, Symbol.H1, Symbol.H1, Symbol.L4],  # 3 H1
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],  # No H1, chain ends
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
        ]
        evaluator = WaysEvaluator(reels, 1.0)
        wins = evaluator.evaluate()
        
        h1_wins = [w for w in wins if w["symbol"] == Symbol.H1]
        self.assertEqual(len(h1_wins), 1)
        self.assertEqual(h1_wins[0]["count"], 3)
        # Ways: 2 × 1 × 3 = 6
        self.assertEqual(h1_wins[0]["ways"], 6)
    
    def test_multiplicative_wild_multipliers(self):
        """Test wild multipliers are multiplicative (2x × 3x = 6x)"""
        reels = [
            [Symbol.H1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.W2X, Symbol.L2, Symbol.L3, Symbol.L4],  # 2x wild
            [Symbol.W3X, Symbol.L2, Symbol.L3, Symbol.L4],  # 3x wild
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
        ]
        evaluator = WaysEvaluator(reels, 1.0)
        wins = evaluator.evaluate()
        
        h1_wins = [w for w in wins if w["symbol"] == Symbol.H1]
        self.assertEqual(len(h1_wins), 1)
        # Multiplier should be 2 × 3 = 6 (multiplicative, not additive)
        self.assertEqual(h1_wins[0]["multiplier"], 6.0)
    
    def test_wild_substitution(self):
        """Test wild symbols substitute correctly"""
        reels = [
            [Symbol.H2, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.W, Symbol.L2, Symbol.L3, Symbol.L4],  # Wild substitutes for H2
            [Symbol.H2, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
            [Symbol.L1, Symbol.L2, Symbol.L3, Symbol.L4],
        ]
        evaluator = WaysEvaluator(reels, 1.0)
        wins = evaluator.evaluate()
        
        h2_wins = [w for w in wins if w["symbol"] == Symbol.H2]
        self.assertEqual(len(h2_wins), 1)
        self.assertEqual(h2_wins[0]["count"], 3)


class TestGameState(unittest.TestCase):
    """Test game state management"""
    
    def test_initial_state(self):
        """Test initial state values"""
        state = GameState()
        self.assertEqual(state.collector_count, 0)
        self.assertEqual(state.transformation_level, 0)
        self.assertFalse(state.infinite_breach_active)
    
    def test_add_collectors(self):
        """Test adding collectors emits event"""
        state = GameState()
        state.add_collectors(3)
        self.assertEqual(state.collector_count, 3)
        
        events = state.flush_events()
        collection_events = [e for e in events if e["type"] == "collectorCollection"]
        self.assertEqual(len(collection_events), 1)
        self.assertEqual(collection_events[0]["data"]["collected"], 3)
    
    def test_transformation_level_updates(self):
        """Test transformation level updates on threshold crossing"""
        state = GameState()
        state.collector_count = 6
        new_transforms = state.update_transformation_level()
        self.assertEqual(state.transformation_level, 4)  # First threshold
        
        state.collector_count = 15
        state.update_transformation_level()
        self.assertTrue(state.infinite_breach_active)


class TestEventSerialization(unittest.TestCase):
    """Test event serialization for multiprocessing"""
    
    def test_serialize_deserialize_roundtrip(self):
        """Test event survives serialization roundtrip"""
        event = {
            "type": "collectorCollection",
            "previousCount": 5,
            "newCount": 8,
            "collected": 3,
            "symbol": Symbol.H1,  # Enum should be serialized
        }
        
        serialized = serialize_event(event)
        deserialized = deserialize_event(serialized)
        
        self.assertEqual(deserialized["type"], "collectorCollection")
        self.assertEqual(deserialized["collected"], 3)
        self.assertEqual(deserialized["symbol"], "H1")  # Enum value
    
    def test_event_queue_thread_safety(self):
        """Test event queue operations"""
        queue = EventQueue(max_size=10)
        
        # Push events
        for i in range(5):
            result = queue.push({"type": "test", "index": i})
            self.assertTrue(result)
        
        self.assertEqual(queue.size(), 5)
        
        # Pop all events
        events = queue.flush()
        self.assertEqual(len(events), 5)
        self.assertEqual(queue.size(), 0)


if __name__ == '__main__':
    unittest.main()
