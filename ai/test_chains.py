import sys, os
sys.path.insert(0, r"D:\CP GPU\ai")
from generate import load_model, generate_response

model, meta = load_model()

conversation_series = [
    # Test 1: Shopkeeper Alibi Follow-up Chain
    ("SHOPKEEPER", "where were you at the time of the robbery"),
    ("SHOPKEEPER", "are you sure? can anyone vouch for you?"),
    ("SHOPKEEPER", "did you stay inside after that?"),

    # Test 2: Theft / Clue Follow-up Chain
    ("SHOPKEEPER", "tell me what happened last night"),
    ("SHOPKEEPER", "how did they get in? was the lock picked?"),
    ("SHOPKEEPER", "what was in the vault?"),

    # Test 3: Guard Patrol Follow-up Chain
    ("GUARD", "where were you during the robbery?"),
    ("GUARD", "did you fall asleep? be honest!"),
    ("GUARD", "why were you dizzy? was your drink spiked?"),

    # Test 4: Kid Sighting Follow-up Chain
    ("KID", "what did you see last night?"),
    ("KID", "who were the shadows? tell me more!"),
    ("KID", "did they drop anything? any clues?")
]

print("="*70)
print("MULTI-TURN PROGRESSIVE FOLLOW-UP TEST")
print("="*70)

current_npc = None
for npc, q in conversation_series:
    if npc != current_npc:
        print(f"\n>>> INTERROGATING {npc} <<<")
        current_npc = npc
    resp = generate_response(model, meta, npc, "LOW", "none", "friendly", q)
    print(f"Player: \"{q}\"")
    print(f"{npc}: {resp}\n")
