import sys, os
sys.path.insert(0, r"D:\CP GPU\ai")
from generate import load_model, generate_response

model, meta = load_model()

queries = [
    ("SHOPKEEPER", "tier1", "where were you at the time of the robbery"),
    ("SHOPKEEPER", "tier2", "are you sure? can anyone vouch for you?"),
    ("SHOPKEEPER", "tier3", "did you stay inside after that?"),
    ("GUARD", "tier1", "where were you during the robbery?"),
    ("GUARD", "tier2", "did you fall asleep? be honest!"),
    ("GUARD", "tier3", "why were you dizzy? was your drink spiked?"),
    ("KID", "tier1", "what happened last night?"),
    ("KID", "tier2", "what did you see?"),
    ("KID", "tier3", "who were the shadows? tell me more!"),
    ("KID", "tier2", "what was on the paper?"),
    ("KID", "tier3", "where are they hiding the loot?")
]

print("="*70)
print("TESTING ACCURATE TIER-INDEXED MEMORY RESPONSES")
print("="*70)
for npc, tier, q in queries:
    resp = generate_response(model, meta, npc, "LOW", tier, "friendly", q)
    print(f"[{npc} | {tier}] Player: \"{q}\"")
    print(f"{npc}: {resp}\n")
