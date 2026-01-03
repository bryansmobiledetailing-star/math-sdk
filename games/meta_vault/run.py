"""
Meta Vault - Main simulation runner

Run simulations with:
    cd games/meta_vault
    python run.py

Or from the root directory:
    make run GAME=meta_vault
"""

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

# Optional imports - may not be available in all setups
try:
    from optimization_program.run_script import OptimizationExecution
    HAS_OPTIMIZATION = True
except ImportError:
    HAS_OPTIMIZATION = False

try:
    from utils.game_analytics.run_analysis import create_stat_sheet
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False


if __name__ == "__main__":
    # ============================================
    # SIMULATION CONFIGURATION
    # ============================================
    
    # Threading configuration
    num_threads = 10        # Number of parallel threads for simulation
    rust_threads = 20       # Threads for Rust optimization (if used)
    batching_size = 10000   # Simulations per batch
    compression = True      # Compress output files
    profiling = False       # Enable performance profiling
    
    # Number of simulations per bet mode
    # Increase for more accurate RTP calculations
    num_sim_args = {
        "base": int(1e6),    # 1,000,000 base game simulations
        "bonus": int(1e4),   # 10,000 bonus buy simulations
    }
    
    # What to run
    run_conditions = {
        "run_sims": True,            # Run simulations
        "run_optimization": True,    # Run RTP optimization (requires Rust)
        "run_analysis": False,       # Generate analytics report
        "upload_data": False,        # Upload to AWS (requires credentials)
    }
    
    # Which bet modes to process
    target_modes = ["base", "bonus"]  # Process both bet modes
    
    # ============================================
    # INITIALIZATION
    # ============================================
    
    print("=" * 60)
    print("META VAULT - Math Engine Simulation")
    print("=" * 60)
    print(f"\nGame ID: meta_vault")
    print(f"Win Type: Ways (1024 ways)")
    print(f"Grid: 5x4")
    print(f"\nMechanics:")
    print("  - Gold Collection (free spins)")
    print("  - Symbol Transformation (H1->V at 4G, H2->V at 7G, etc.)")
    print("  - Wild Multipliers (x2/x3, multiplicative)")
    print("-" * 60)
    
    # Initialize config and game state
    config = GameConfig()
    gamestate = GameState(config)
    
    # Always initialize optimization setup to populate math_config.json
    optimization_setup_class = OptimizationSetup(config)
    
    print(f"\nTarget RTP: {config.rtp * 100}%")
    print(f"Win Cap: {config.wincap}x")
    print(f"Simulations: {num_sim_args}")
    print("-" * 60)
    
    # Initialize optimization if needed
    if run_conditions["run_optimization"]:
        if not HAS_OPTIMIZATION:
            print("Warning: Optimization not available (Rust/Cargo not installed)")
    
    # ============================================
    # RUN SIMULATIONS
    # ============================================
    
    if run_conditions["run_sims"]:
        print("\n🎰 Running Simulations...")
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )
        print("✅ Simulations complete!")
    
    # Generate configuration files
    print("\n📝 Generating config files...")
    generate_configs(gamestate)
    print("✅ Config files generated!")
    
    # ============================================
    # OPTIMIZATION (Optional)
    # ============================================
    
    if run_conditions["run_optimization"]:
        if HAS_OPTIMIZATION:
            print("\n⚙️ Running Optimization...")
            OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
            generate_configs(gamestate)
            print("✅ Optimization complete!")
        else:
            print("\n⚠️ Skipping optimization (Rust not installed)")
    
    # ============================================
    # ANALYTICS (Optional)
    # ============================================
    
    if run_conditions["run_analysis"]:
        if HAS_ANALYTICS:
            print("\n📊 Generating Analytics...")
            custom_keys = [
                {"symbol": "scatter"},
                {"event": "transformation"},
            ]
            create_stat_sheet(config.game_id, custom_keys=custom_keys)
            print("✅ Analytics generated!")
        else:
            print("\n⚠️ Skipping analytics (module not available)")
    
    # ============================================
    # UPLOAD (Optional)
    # ============================================
    
    if run_conditions["upload_data"]:
        try:
            from utils.upload_files import upload_to_aws
            print("\n☁️ Uploading to AWS...")
            upload_items = {
                "books": True,
                "lookup_tables": True,
                "force_files": True,
                "config_files": True,
            }
            upload_to_aws(gamestate, target_modes, upload_items)
            print("✅ Upload complete!")
        except ImportError:
            print("\n⚠️ Skipping upload (AWS module not available)")
        except Exception as e:
            print(f"\n❌ Upload failed: {e}")
    
    print("\n" + "=" * 60)
    print("META VAULT - Simulation Complete!")
    print("=" * 60)
    print("\n📈 Next Steps:")
    print("  1. Check output files in games/meta_vault/output/")
    print("  2. Review RTP and hit frequency in simulation results")
    print("  3. Integrate with Web SDK for frontend")
    print("  4. Run more simulations for production (1e6+)")
