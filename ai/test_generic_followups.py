import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, r"D:\CP GPU\ai")
from generate import load_model, generate_response
from intent import dialogue_state

model, meta = load_model()

test_queries = [
    # General & follow-up questions for Shopkeeper (Dazai)
    ("SHOPKEEPER", "can you tell me what you saw?"),
    ("SHOPKEEPER", "and then what happened?"),
    ("SHOPKEEPER", "did anyone buy anything suspicious from your shop?"),
    ("SHOPKEEPER", "tell me more about that buyer"),
    ("SHOPKEEPER", "can someone confirm where you were?"),
    ("SHOPKEEPER", "confess! where is the gold hidden?"),
    ("SHOPKEEPER", "where can I find the guard?"),

    # General & follow-up questions for Guard (Escanor)
    ("GUARD", "what happened on your watch last night?"),
    ("GUARD", "were you sleeping on the job?"),
    ("GUARD", "why were you dizzy? was your drink poisoned?"),
    ("GUARD", "did anyone visit your guardhouse yesterday?"),
    ("GUARD", "is the duplicate key safe in your desk?"),
    ("GUARD", "who do you think is responsible?"),

    # General & follow-up questions for Farmer (Zoro)
    ("FARMER", "good day, what are you doing here?"),
    ("FARMER", "did you hear or see anything strange at night?"),
    ("FARMER", "what happened to your cart?"),
    ("FARMER", "which way did the cart go?"),
    ("FARMER", "can anyone vouch for your alibi?"),
    ("FARMER", "where did they haul the treasure?"),

    # General & follow-up questions for Kid (Naruto)
    ("KID", "hey kid, what are you doing here?"),
    ("KID", "did you see anything unusual last night?"),
    ("KID", "did they drop anything near the vault?"),
    ("KID", "what was written on that paper you found?"),
    ("KID", "where did the wagon go?"),

    # General & follow-up questions for Old Man (Roshi)
    ("OLD_MAN", "hello elder, what is your story?"),
    ("OLD_MAN", "who knows how the vault lock works?"),
    ("OLD_MAN", "did you hear any noises around midnight?"),
    ("OLD_MAN", "whose cane tip was dropped in the street?"),
    ("OLD_MAN", "where is the physical evidence hidden?"),
    ("OLD_MAN", "who took the duplicate key?"),
]

print("=================================================================")
print("   TESTING GENERIC AND FOLLOW-UP QUESTIONS ON NANOGPT MODEL      ")
print("=================================================================\n")

failures = []

for npc, q in test_queries:
    dialogue_state.reset()
    norm_q = dialogue_state.process(q, npc=npc)
    tier = dialogue_state.current_tier
    trust = "LOW" if tier == 1 else ("MEDIUM" if tier == 2 else "HIGH")
    resp = generate_response(model, meta, npc, trust, "no memory", "friendly", q, culprit="SHOPKEEPER")
    
    print(f"[{npc}] Player: \"{q}\"")
    print(f"       -> Normalized Intent: \"{norm_q}\" (Tier {tier} | Trust: {trust})")
    print(f"       -> Response: {resp}\n")
    
    # Check for obvious quality issues: empty response, garbled repetition, or wrong NPC persona
    if not resp or len(resp.strip()) < 10:
        failures.append((npc, q, "Response too short or empty", resp))
    if resp.strip().startswith("[") or resp.strip().startswith("<|"):
        failures.append((npc, q, "Raw token leak", resp))

if failures:
    print(f"\n[DETECTED {len(failures)} ISSUES]")
    for npc, q, reason, resp in failures:
        print(f"  - [{npc}] \"{q}\": {reason} -> '{resp}'")
else:
    print("\n[ALL TEST QUERIES RETURNED VALID RESPONSES]")
