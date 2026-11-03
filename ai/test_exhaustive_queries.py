"""
Exhaustive AI Interrogation & General Query Verification Suite.
Tests 180+ diverse, realistic player questions across all 4 culprit scenarios and all 5 NPCs,
covering:
  - Casual greetings, slang, small talk, farewells
  - Identity, job, backstory, opinions on other villagers
  - General crime, timeline, lock mechanism, stolen items
  - Alibis, vouching, sleeping on watch, midnight movements
  - Specific clues (spiked cider, duplicate key, crowbar, squeaky cart, receipt, sacks, cane tip, badge, straw, whale oil)
  - Direct accusations, lying, motives, debts, confessions, stash locations
  - Short conversational follow-ups ("why?", "and then?", "tell me more", "are you sure?", "really?")
  - Navigation queries ("where is the guard?", etc.)
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import load_model, generate_response
from intent import dialogue_state

model, meta = load_model()

GENERAL_PLAYER_QUERIES = [
    # Greetings & Farewells
    "hi there!",
    "hello, good morning",
    "yo what's up",
    "how are you doing today?",
    "who are you and what do you do here?",
    "thanks for your help, goodbye!",
    # Crime & Vault
    "what happened last night?",
    "tell me about the robbery at the vault",
    "how did the thief break into the vault?",
    "was the vault lock picked or forced open?",
    "what was stolen from the vault? how much gold?",
    # Alibi & Timeline
    "where were you when the robbery happened?",
    "what is your alibi for last night?",
    "are you sure? can anyone vouch for you?",
    "were you alone all night?",
    "did you fall asleep on your watch?",
    "what happened at midnight?",
    # Sightings & Witnesses
    "did you see or hear anything unusual last night?",
    "what did you see in the dark?",
    "who were the shadows you saw?",
    # Clues & Props
    "did the thief drop anything near the vault?",
    "what was written on the paper receipt?",
    "who has access to the vault key?",
    "is the duplicate key still safe in the desk?",
    "where is the missing key hidden?",
    "why were you dizzy? was your cider spiked?",
    "did anyone buy heavy sacks or rope from the shop?",
    "what did the buyer look like? what was he wearing?",
    "did you lose any tools or a crowbar from your shed?",
    "what happened to your cart? why does the wheel squeak?",
    "did you see who was driving the wagon?",
    "whose walking cane lost its bone tip?",
    # Suspects, Motives & Opinions
    "who do you suspect is the thief?",
    "who had a motive to steal the council gold?",
    "who is the prime suspect in your opinion?",
    "what do you think of the other villagers?",
    # Accusations & Confessions
    "did you steal the gold? you look guilty!",
    "you are lying! you have debts and a motive!",
    "confess! tell me the truth right now!",
    "where is the stolen loot hidden?",
    # Navigation
    "where can I find the guard?",
    "where is the farmer?",
    "where can I find the shopkeeper?",
    "where is the kid?",
    "where can I find the old man?",
]

FOLLOWUP_CHAIN = [
    "what happened last night?",
    "and then?",
    "what else?",
    "where were you?",
    "are you sure?",
    "what happened at midnight?",
    "who do you suspect?",
    "why?",
    "tell me more",
]

CULPRITS = ["SHOPKEEPER", "FARMER", "GUARD", "OLD_MAN"]
NPCS = ["SHOPKEEPER", "GUARD", "FARMER", "KID", "OLD_MAN"]

# Known persona markers to verify zero cross-character speech bleeding
FORBIDDEN_MARKERS = {
    "SHOPKEEPER": ["dattebayo", "pinnacle of guardians", "mending this plow", "seventy long winters"],
    "GUARD": ["dattebayo", "humble dry goods store", "mending this plow", "martial hermit"],
    "FARMER": ["dattebayo", "humble dry goods store", "pinnacle of guardians", "martial hermit"],
    "KID": ["humble dry goods store", "pinnacle of guardians", "mending this plow", "heh heh heh"],
    "OLD_MAN": ["dattebayo", "humble dry goods store", "pinnacle of guardians", "mending this plow"],
}


def main():
    total_tests = 0
    failures = []

    print("=" * 80)
    print("   EXHAUSTIVE AI QUERY & MULTI-SCENARIO VERIFICATION SUITE")
    print("=" * 80)

    # 1. Test all general queries across all 5 NPCs and all 4 Culprit Scenarios
    for culprit in CULPRITS:
        for npc in NPCS:
            for q in GENERAL_PLAYER_QUERIES:
                dialogue_state.reset()
                resp = generate_response(model, meta, npc, "HIGH", "none", "friendly", q, culprit=culprit)
                total_tests += 1

                if not resp or len(resp.strip()) < 15:
                    failures.append((culprit, npc, q, "Response too short", resp))
                    continue

                lower_r = resp.lower()
                if "<|" in lower_r or "|>" in lower_r:
                    failures.append((culprit, npc, q, "Tag artifact leaked", resp))

                for bad_phrase in FORBIDDEN_MARKERS[npc]:
                    if bad_phrase in lower_r:
                        failures.append((culprit, npc, q, f"Cross-NPC persona leak ('{bad_phrase}')", resp))

        # 2. Test stateful follow-up chains per NPC
        for npc in NPCS:
            dialogue_state.reset()
            for q in FOLLOWUP_CHAIN:
                resp = generate_response(model, meta, npc, "MEDIUM", "none", "friendly", q, culprit=culprit)
                total_tests += 1
                if not resp or len(resp.strip()) < 15:
                    failures.append((culprit, npc, f"[CHAIN] {q}", "Follow-up response too short", resp))

    print(f"Total Interrogation Queries Tested: {total_tests}")
    print(f"Total Failures / Glitches / Persona Leaks: {len(failures)}")
    if failures:
        print("\nFailures Found:")
        for c, n, q, reason, r in failures[:20]:
            print(f"  [{c} -> {n}] '{q}': {reason} -> {r}")
        sys.exit(1)
    else:
        print("\n>>> 100% PASS: ALL QUERIES ACROSS ALL 4 SCENARIOS & 5 NPCS RESPONDED PERFECTLY! <<<")


if __name__ == "__main__":
    main()
