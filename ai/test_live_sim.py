import sys, os
sys.path.insert(0, r"D:\CP GPU\ai")
from generate import load_model, generate_response
from intent import dialogue_state

model, meta = load_model()

questions = [
    ("SHOPKEEPER", "hi shopkeeper"),
    ("SHOPKEEPER", "where were you at the time of the robbery"),
    ("SHOPKEEPER", "are you sure? can anyone vouch for you?"),
    ("SHOPKEEPER", "did you stay inside after that?"),
    ("SHOPKEEPER", "who do you suspect?"),
    ("SHOPKEEPER", "who bought the sack?"),
    ("SHOPKEEPER", "did you steal it?"),
    ("GUARD", "where were you during the robbery?"),
    ("GUARD", "did you fall asleep? be honest!"),
    ("GUARD", "why were you dizzy? was your drink spiked?")
]

print("="*70)
print("LIVE SIMULATION: NATURAL MULTI-TURN INTERROGATION")
print("="*70)

current_npc = None
for npc, q in questions:
    if npc != current_npc:
        dialogue_state.current_depth = 0
        dialogue_state.current_topic = "GREETING"
        print(f"\n>>> INTERROGATING {npc} <<<")
        current_npc = npc
    resp = generate_response(model, meta, npc, "LOW", "none", "friendly", q)
    print(f"Player: \"{q}\"")
    print(f"{npc} [Depth {dialogue_state.current_depth + 1}]: {resp}\n")
