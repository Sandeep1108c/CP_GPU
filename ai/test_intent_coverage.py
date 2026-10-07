import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, r"D:\CP GPU\ai")
from generate import load_model, generate_response
from intent import dialogue_state, get_scenario_query_tier

model, meta = load_model()

# Broad battery of realistic questions asked by players, judges, and evaluators
questions_to_test = [
    # 1. Broad & Open-Ended Theft Inquiries
    ("SHOPKEEPER", "what happened last night?"),
    ("SHOPKEEPER", "what was stolen from the vault?"),
    ("SHOPKEEPER", "how much gold was taken?"),
    ("SHOPKEEPER", "how did they break in? was the lock picked?"),
    ("GUARD", "how did they enter the vault?"),
    ("GUARD", "was the vault door forced open?"),
    ("OLD_MAN", "what happened to the vault?"),
    ("OLD_MAN", "how was the lock opened?"),

    # 2. Suspect & Motive Inquiries
    ("SHOPKEEPER", "who do you think is the thief?"),
    ("SHOPKEEPER", "who had a motive to steal the taxes?"),
    ("SHOPKEEPER", "who was acting suspicious yesterday?"),
    ("GUARD", "who is the prime suspect?"),
    ("GUARD", "why would Zoro steal the gold?"),
    ("FARMER", "who do you suspect did it?"),
    ("OLD_MAN", "who is the thief?"),

    # 3. Store, Purchases & Sacks (Shopkeeper specific)
    ("SHOPKEEPER", "did anyone buy anything suspicious from your shop?"),
    ("SHOPKEEPER", "did someone buy heavy sacks or rope from you?"),
    ("SHOPKEEPER", "what did the customer who bought the rope look like?"),
    ("SHOPKEEPER", "what was the buyer wearing?"),
    ("SHOPKEEPER", "tell me more about that buyer"),

    # 4. Alibis & Timeline Inquiries
    ("SHOPKEEPER", "where were you when the robbery took place?"),
    ("SHOPKEEPER", "were you alone in your shop all night?"),
    ("SHOPKEEPER", "did you step outside into the lane?"),
    ("SHOPKEEPER", "can anyone confirm where you were?"),
    ("GUARD", "what were you doing during your patrol?"),
    ("GUARD", "did you fall asleep on your watch?"),
    ("GUARD", "why were you dizzy? was your drink poisoned?"),
    ("FARMER", "where were you last night?"),
    ("FARMER", "were you asleep the whole night in your bed?"),
    ("FARMER", "can anyone vouch for your alibi?"),
    ("OLD_MAN", "where were you last night?"),

    # 5. Keys, Desk & Vault Mechanisms
    ("GUARD", "who has access to the duplicate key?"),
    ("GUARD", "is the duplicate key still in your desk?"),
    ("GUARD", "who was near your desk yesterday morning?"),
    ("GUARD", "did someone steal the key from your drawer?"),
    ("OLD_MAN", "who has the key to the vault?"),
    ("OLD_MAN", "where is the missing duplicate key?"),
    ("OLD_MAN", "who designed the vault lock forty years ago?"),

    # 6. Tools, Cart & Footprints (Farmer / Kid / Old Man)
    ("FARMER", "did you lose any tools from your shed?"),
    ("FARMER", "what happened to your cart?"),
    ("FARMER", "why is the left wheel squeaking?"),
    ("FARMER", "who was driving the cart?"),
    ("FARMER", "which way did the tracks lead?"),
    ("KID", "what did you see while scouting on the roofs?"),
    ("KID", "which way did the cart go?"),
    ("OLD_MAN", "did you notice any strange wheel ruts?"),

    # 7. Physical Evidence, Clues & Dropped Items
    ("KID", "did they drop anything near the vault steps?"),
    ("KID", "what was written on the receipt you found?"),
    ("KID", "what did the receipt smell like?"),
    ("OLD_MAN", "whose cane tip was found in the street?"),
    ("OLD_MAN", "where is the physical evidence hidden?"),

    # 8. Accusations, Pressure & Confessions
    ("SHOPKEEPER", "you look guilty! did you steal it?"),
    ("SHOPKEEPER", "your shop is in debt! you have a motive!"),
    ("SHOPKEEPER", "confess! tell me the truth!"),
    ("SHOPKEEPER", "where did you hide the stolen gold?"),
    ("FARMER", "confess, where did you hide the loot?"),
    ("GUARD", "confess Escanor, you staged the theft!"),
    ("OLD_MAN", "confess Master Roshi, where is the treasure?"),

    # 9. Follow-Up Words & Conversational Probing
    ("SHOPKEEPER", "and then?"),
    ("SHOPKEEPER", "what else?"),
    ("SHOPKEEPER", "tell me more"),
    ("GUARD", "why?"),
    ("GUARD", "are you sure?"),
    ("FARMER", "really?"),
    ("KID", "what happened next?"),

    # 10. Greetings & Navigation
    ("SHOPKEEPER", "hello there!"),
    ("SHOPKEEPER", "where can I find the guard?"),
    ("GUARD", "where can I find the farmer?"),
    ("FARMER", "where can I find the kid?"),
    ("KID", "where can I find the old man?"),
]

print(f"Running intent and response evaluation across {len(questions_to_test)} queries...\n")

issues = []

for npc, q in questions_to_test:
    dialogue_state.reset()
    norm_q = dialogue_state.process(q, npc=npc)
    tier = dialogue_state.current_tier
    trust = "LOW" if tier == 1 else ("MEDIUM" if tier == 2 else "HIGH")
    
    # Pass normalized query and corresponding tier memory
    resp = generate_response(model, meta, npc, trust, f"tier{tier}", "friendly", norm_q, culprit="SHOPKEEPER")
    
    # Print out summary
    print(f"[{npc}] \"{q}\"")
    print(f"       -> Normalized: \"{norm_q}\" (Tier {tier})")
    print(f"       -> Response: {resp}\n")
    
    # Check if normalized query makes sense for the question
    q_lower = q.lower()
    if "buy" in q_lower or "bought" in q_lower or "rope" in q_lower or "sack" in q_lower:
        if norm_q not in ["tell me about the buyer", "who bought the sack", "did you sell any heavy sacks"]:
            issues.append((npc, q, f"Buyer inquiry routed to '{norm_q}' instead of sack/buyer intent"))
            
    if "wearing" in q_lower or "look like" in q_lower:
        if norm_q not in ["tell me about the buyer", "who were the shadows", "did you see someone outside", "what did you see"]:
            issues.append((npc, q, f"Appearance inquiry routed to '{norm_q}'"))
            
    if ("stolen" in q_lower or "how much" in q_lower) and "hide" not in q_lower and "loot" not in q_lower:
        if norm_q not in ["what was in the vault", "what happened last night", "what was stolen"]:
            issues.append((npc, q, f"Vault contents inquiry routed to '{norm_q}'"))

print("=" * 70)
print(f"EVALUATION COMPLETE: {len(issues)} INTENT ROUTING ISSUES DETECTED")
print("=" * 70)
for npc, q, reason in issues:
    print(f"  * [{npc}] \"{q}\" -> {reason}")
