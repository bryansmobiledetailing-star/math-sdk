"""Analyze Meta Vault simulation results."""

import csv
import json
from collections import Counter

print("=" * 60)
print("META VAULT - SIMULATION RESULTS ANALYSIS")
print("=" * 60)

# Read lookup table for base mode
with open('library/lookup_tables/lookUpTable_base.csv', 'r') as f:
    reader = csv.reader(f)
    data = list(reader)

# Payouts in lookup table are in credits where 100 credits = 1 bet (1x)
# RTP = Total Payout / Total Wagered = Sum(payouts) / (sims * 100)
CREDITS_PER_BET = 100

total_sims = len(data)
payouts_credits = [float(row[2]) for row in data]
payouts_x = [c / CREDITS_PER_BET for c in payouts_credits]  # Convert to multipliers
total_payout_credits = sum(payouts_credits)
total_payout_x = total_payout_credits / CREDITS_PER_BET
avg_payout_x = total_payout_x / total_sims
# RTP is the average return, expressed as percentage
rtp_percent = avg_payout_x  # Already a ratio, e.g. 0.96 = 96% RTP

print(f"\n📊 BASE GAME STATISTICS")
print("-" * 40)
print(f"Total Simulations: {total_sims:,}")
print(f"Total Payout: {total_payout_x:,.2f}x ({total_payout_credits:,.0f} credits)")
print(f"Average Payout: {avg_payout_x:.4f}x per spin")
print(f"Simulated RTP: {rtp_percent:.2f}%")

# Win distribution (using payouts_x - multipliers)
zero_wins = sum(1 for p in payouts_x if p == 0)
tiny_wins = sum(1 for p in payouts_x if 0 < p <= 1)
small_wins = sum(1 for p in payouts_x if 1 < p <= 10)
medium_wins = sum(1 for p in payouts_x if 10 < p <= 100)
big_wins = sum(1 for p in payouts_x if 100 < p <= 1000)
huge_wins = sum(1 for p in payouts_x if 1000 < p <= 10000)
mega_wins = sum(1 for p in payouts_x if p > 10000)

max_win = max(payouts_x)
nonzero = [p for p in payouts_x if p > 0]
min_win = min(nonzero) if nonzero else 0
avg_win = sum(nonzero) / len(nonzero) if nonzero else 0

print(f"\nMax Single Win: {max_win:,.2f}x")
print(f"Min Non-Zero Win: {min_win:.4f}x")
print(f"Avg Win (when winning): {avg_win:.2f}x")

print(f"\n📈 WIN DISTRIBUTION")
print("-" * 40)
print(f"Dead Spins (0x):    {zero_wins:,} ({zero_wins/total_sims*100:.1f}%)")
print(f"Tiny (0-1x):        {tiny_wins:,} ({tiny_wins/total_sims*100:.1f}%)")
print(f"Small (1-10x):      {small_wins:,} ({small_wins/total_sims*100:.1f}%)")
print(f"Medium (10-100x):   {medium_wins:,} ({medium_wins/total_sims*100:.1f}%)")
print(f"Big (100-1000x):    {big_wins:,} ({big_wins/total_sims*100:.1f}%)")
print(f"Huge (1000-10000x): {huge_wins:,} ({huge_wins/total_sims*100:.1f}%)")
print(f"Mega (>10000x):     {mega_wins:,} ({mega_wins/total_sims*100:.1f}%)")

# Top 10 highest wins
print(f"\n🏆 TOP 10 WINS")
print("-" * 40)
sorted_payouts = sorted(enumerate(payouts_x), key=lambda x: x[1], reverse=True)[:10]
for i, (sim_id, payout) in enumerate(sorted_payouts, 1):
    print(f"{i}. Sim #{sim_id}: {payout:,.2f}x")

# Read force file
with open('library/forces/force_record_base.json', 'r') as f:
    forces = json.load(f)

# Analyze scatter triggers
scatter_triggers = {}
for force in forces:
    search_dict = {s['name']: s['value'] for s in force['search']}
    if search_dict.get('symbol') == 'scatter':
        gt = search_dict.get('gametype', 'unknown')
        kind = search_dict.get('kind', 'unknown')
        key = f"{gt}_{kind}"
        scatter_triggers[key] = force['timesTriggered']

print(f"\n🎰 SCATTER TRIGGERS")
print("-" * 40)
for key, count in sorted(scatter_triggers.items()):
    hit_rate = total_sims / count if count > 0 else float('inf')
    print(f"{key}: {count:,} triggers (1 in {hit_rate:.0f})")

print("\n" + "=" * 60)
