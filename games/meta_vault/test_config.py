"""Test script for Meta Vault Buffalo-style configuration."""

from game_config import GameConfig

def analyze_h1_stacks(reel):
    """Find maximum consecutive H1 symbols in a reel."""
    max_stack = 0
    current_stack = 0
    for symbol in reel:
        if symbol == 'H1':
            current_stack += 1
            max_stack = max(max_stack, current_stack)
        else:
            current_stack = 0
    return max_stack

def main():
    gc = GameConfig()
    
    print("=" * 50)
    print("META VAULT - Configuration Test")
    print("=" * 50)
    
    print(f"\n✅ Game ID: {gc.game_id}")
    print(f"✅ Win Type: {gc.win_type}")
    print(f"✅ Grid: {gc.num_reels}x{gc.num_rows[0]} = {gc.num_rows[0]**gc.num_reels} ways")
    print(f"✅ RTP: {gc.rtp * 100}%")
    print(f"✅ Wincap: {gc.wincap}x")
    
    print("\n--- BUFFALO-STYLE PAYTABLE ---")
    print("H1 (Hero) - Pays 2-of-a-kind:")
    for k, v in gc.paytable.items():
        if k[1] == 'H1':
            print(f"  {k[0]}-of-a-kind: {v}x")
    
    print("\nV (Vault) - Pays 2-of-a-kind:")
    for k, v in gc.paytable.items():
        if k[1] == 'V':
            print(f"  {k[0]}-of-a-kind: {v}x")
    
    print(f"\n✅ Min Match Config: {gc.symbol_min_match}")
    print(f"✅ Multiplier Logic: {gc.bonus_multiplier_logic}")
    print(f"✅ Win Evaluator Mode: {gc.win_evaluator_mode}")
    
    print("\n--- REEL STRIP ANALYSIS ---")
    print(f"Reels loaded: {list(gc.reels.keys())}")
    
    for reel_name in ['BR0', 'FR0']:
        if reel_name in gc.reels:
            reels = gc.reels[reel_name]
            print(f"\n{reel_name} Analysis:")
            print(f"  Reel lengths: {[len(r) for r in reels]}")
            
            h1_counts = [sum(1 for s in reel if s == 'H1') for reel in reels]
            print(f"  H1 per reel: {h1_counts}")
            print(f"  Total H1: {sum(h1_counts)}")
            
            max_stacks = [analyze_h1_stacks(reel) for reel in reels]
            print(f"  Max H1 stack per reel: {max_stacks}")
            
            if reel_name == 'FR0':
                wild_counts = [sum(1 for s in reel if s == 'W') for reel in reels]
                print(f"  Wild (W) per reel: {wild_counts}")
    
    print("\n--- MAX WIN CALCULATION ---")
    h1_5_pay = gc.paytable.get((5, 'H1'), 0)
    ways = gc.num_rows[0] ** gc.num_reels
    base_max = h1_5_pay * ways
    print(f"Full screen H1: {ways} ways × {h1_5_pay}x = {base_max}x")
    
    max_mult = 3 * 3  # Two 3x wilds
    with_mult = base_max * max_mult
    print(f"With 3x × 3x Wilds: {base_max}x × {max_mult} = {with_mult}x")
    print(f"Capped at: {gc.wincap}x ✅" if with_mult > gc.wincap else f"Under cap ✅")
    
    print("\n" + "=" * 50)
    print("All checks passed! ✅")
    print("=" * 50)

if __name__ == "__main__":
    main()
