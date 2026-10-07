"""
Stateful Multi-Tier Intent Matcher for nanoGPT Game Dialogue.
Tracks dialogue topic, depth, and tier (Tier 1 -> Tier 2 -> Tier 3) across successive turns,
allowing NPCs to reveal deeper clues and alibi details when pressed by the player.
Now strictly NPC-aware so characters never speak each other's dialogue lines.
"""

import re
import os
import sys

# Load scenario dataset for dynamic scenario-aware tier resolution
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if data_path not in sys.path:
    sys.path.insert(0, data_path)

try:
    from generate_multi_culprit_dataset import SCENARIOS
except ImportError:
    SCENARIOS = {}


def get_scenario_query_tier(culprit: str, npc: str, query: str) -> int:
    """Returns the true dataset tier (1, 2, or 3) for a query given the active culprit scenario and target NPC."""
    q_clean = query.lower().strip()
    entries = SCENARIOS.get(culprit, {}).get(npc, [])
    # 1. Exact match in dataset
    for tier, qs, resp in entries:
        for pattern in qs:
            if pattern.lower() == q_clean:
                return tier
    # 2. Substring match
    for tier, qs, resp in entries:
        for pattern in qs:
            if pattern.lower() in q_clean or q_clean in pattern.lower():
                return tier
    # 3. Fallback to global static mapping
    return QUERY_TO_TIER.get(q_clean, 1)


# NPC-specific topic progression tiers to avoid cross-character dialogue leaks
NPC_TOPIC_TIERS = {
    "SHOPKEEPER": {
        "ALIBI": [
            "where were you at the time of robbery",
            "are you sure",
            "did you stay inside after that"
        ],
        "SACKS": [
            "who bought the sack",
            "tell me about the buyer",
            "tell me the truth"
        ],
        "SIGHTINGS": [
            "did you see anything",
            "what kind of sounds",
            "did you see shadows"
        ],
        "THEFT": [
            "what happened last night",
            "how did they get in",
            "what was in the vault"
        ],
        "SUSPECTS": [
            "who do you suspect",
            "tell me who you suspect",
            "who bought the sack"
        ],
        "ACCUSATION": [
            "did you steal it",
            "you have a motive",
            "tell me the truth"
        ],
        "GREETING": [
            "hi",
            "how are you",
            "who are you"
        ]
    },
    "GUARD": {
        "ALIBI": [
            "where were you during the robbery",
            "were you sleeping",
            "why were you dizzy"
        ],
        "KEYS": [
            "who was near your desk",
            "is the duplicate key safe",
            "who is the prime suspect"
        ],
        "PATROL": [
            "how goes the patrol",
            "were you sleeping",
            "why were you dizzy"
        ],
        "THEFT": [
            "what happened last night",
            "how did they enter",
            "who had access"
        ],
        "SUSPECTS": [
            "who did it",
            "who visited the guard house",
            "who is the prime suspect"
        ],
        "GREETING": [
            "halt",
            "how goes the patrol",
            "who are you"
        ]
    },
    "FARMER": {
        "ALIBI": [
            "where were you last night",
            "were you asleep the whole night",
            "what happened at midnight"
        ],
        "TOOLS": [
            "did you lose any tools",
            "about that cart",
            "where did the wagon go"
        ],
        "CART": [
            "about that cart",
            "did you see who was driving",
            "who took the cart"
        ],
        "LOOT": [
            "about that cart",
            "where did the wagon go",
            "where is the loot"
        ],
        "SUSPECTS": [
            "who did it",
            "who do you suspect",
            "who took the cart"
        ],
        "GREETING": [
            "hi",
            "how is the harvest",
            "who are you"
        ]
    },
    "KID": {
        "SIGHTINGS": [
            "did you see anything last night",
            "did you see anyone",
            "who were the shadows"
        ],
        "CLUES": [
            "did they drop anything",
            "what was on the paper",
            "where are they hiding the loot"
        ],
        "THEFT": [
            "what happened last night",
            "did you see anything last night",
            "who were the shadows"
        ],
        "GREETING": [
            "hey kid",
            "what are you doing",
            "who are you"
        ]
    },
    "OLD_MAN": {
        "SIGHTINGS": [
            "did you see anything",
            "did you see lights",
            "did you see shadows"
        ],
        "THEFT": [
            "what happened last night",
            "what is your story",
            "reveal the truth"
        ],
        "CLUES": [
            "did you hear anything",
            "where is the key",
            "where is the evidence hidden"
        ],
        "KEYS": [
            "who has the key",
            "where is the key",
            "where is the evidence hidden"
        ],
        "SUSPECTS": [
            "who is the thief",
            "who had a motive",
            "reveal the truth"
        ],
        "GREETING": [
            "greetings",
            "what is your story",
            "who are you"
        ]
    }
}

# Explicit mapping of normalized queries to dataset tier.
# Every entry is derived from the SCENARIOS dataset — tier = max tier that
# query appears in across all culprit × NPC combinations.
QUERY_TO_TIER = {
    # ── Tier 1 — Greetings & first-contact surface questions ─────────────────
    "hi": 1, "hello": 1, "hey": 1, "greetings": 1, "good day": 1,
    "halt": 1, "officer": 1,
    "hey guard": 1, "hey farmer": 1, "hey kid": 1, "hey there": 1,
    "what happened": 1, "what happened last night": 1, "tell me what happened": 1,
    "tell me about the robbery": 1, "there was a robbery": 1,
    # "where were you" appears at Tier 1 AND Tier 2 across scenarios;
    # assign Tier 1 so LOW-trust gate correctly surfaces the alibi opener.
    "where were you": 1, "where were you during the robbery": 1,
    "what were you doing": 1, "what were you doing at the time of robbery": 1,
    "what is your alibi": 1,
    "did you lose any tools": 1, "what tools did you lose": 1, "are your tools missing": 1,
    "did you notice anything unusual": 1,
    "did anyone buy unusual supplies": 1,
    "any idea who is it": 1, "who could have done it": 1,
    "you look guilty": 1, "you stole it": 1, "did you do it": 1,

    # ── Tier 2 — Follow-up probing: timeline gaps, odd behaviours ────────────
    # Alibi probing
    "are you sure": 2, "can anyone vouch for you": 2,
    "were you alone": 2, "did you step outside": 2,
    "were you sleeping": 2, "were you asleep the whole night": 2,
    "did you fall asleep": 2, "be honest about your watch": 2, "you fell asleep": 2,
    "how goes the patrol": 2,
    # "where were you last night" is Tier 1 as opener but Tier 2 as press;
    # keep at Tier 2 so a second ask gets deeper alibi detail.
    "where were you last night": 2,
    "what were you doing last night": 2,
    # Sightings / sounds (surface observation)
    "did you see anything": 2, "did you hear anything": 2,
    "what kind of sounds": 2, "did you hear footsteps": 2, "did you hear noises": 2,
    "did you see lights": 2, "did you see someone outside": 2, "did you see anyone": 2,
    "did you see anything last night": 2,
    # Paper / clues (before naming specific clue)
    "did they drop anything": 2, "any evidence": 2, "did you find clues": 2,
    "show me the paper": 2, "what was on the paper": 2, "what did the paper say": 2,
    # Cart / tools
    "about that cart": 2, "is your cart in the barn": 2, "did someone take your cart": 2,
    # Suspects (surface suspicion — before naming names)
    "who is the thief": 2, "who do you think did it": 2,
    "you have a motive": 2, "your shop has debts": 2,
    "you were seen near the vault": 2, "someone who": 2,
    # Accusation — surface accusation without pressing for confession
    "did you steal it": 2, "are you the thief": 2,
    # Keys / access (surface access question, not stash location)
    "who has the key": 2, "how did they get in": 2, "how did they enter": 2,
    "did they pick the lock": 2, "was the door broken": 2,
    "who was near your desk": 2, "who visited the guard house": 2, "who had access": 2,
    # Lock picking / beeswax (leads toward Tier 3 but still Tier 2 in dataset)
    "how did they enter": 2,
    # Small-talk / context
    "how are you": 2, "how are things": 2, "how is business": 2, "how is the harvest": 2,
    "what are you doing": 2, "what is your story": 2,
    # "what did you see" spans Tier 1-3; use Tier 2 as middle ground
    "what did you see": 2,

    # ── Tier 3 — Revelation: physical clues, stash locations, confessions ────
    # Suspicion / naming the culprit
    "who had a motive": 3, "who do you suspect": 3, "tell me who you suspect": 3,
    "who was acting suspicious": 3, "name names": 3, "tell me more": 3,
    "who did it": 3, "who really did it": 3, "who is the prime suspect": 3,
    "tell me who you think took it": 3,
    # Witness deeper testimony
    "were you alone": 3, "can anyone vouch": 3,
    "who was near your desk": 3, "who were the shadows": 3, "did you see their faces": 3,
    "did you see shadows": 3, "who was whistling": 3, "what happened after the whistle": 3,
    # Stash / physical evidence locations
    "where is the key": 3, "where did you hide": 3,
    "where did the wagon go": 3, "where did the cart go": 3,
    "where is the loot": 3, "where are they hiding the loot": 3,
    "where is the evidence hidden": 3,
    # Key-specific clues
    "is the duplicate key safe": 3, "did someone steal the key": 3, "check the desk": 3,
    "who took the cart": 3, "did you see who was driving": 3, "did you check the barn": 3,
    # Cane / Old Man specific — Tier 2: probing observation ("whose cane?")
    # The Tier 3 cane revelation is unlocked by "where is the key" which
    # normalises the intent.py "cane hidden key" pattern to that phrase.
    "whose cane": 2,
    # Shopkeeper / receipt / sacks
    "who bought the sack": 3, "who bought the rope": 3, "tell me about the buyer": 3,
    # Guard dizziness
    "why were you dizzy": 3, "was your drink spiked": 3, "did someone drug you": 3,
    # Vault details
    "what was in the vault": 3, "what was stolen": 3, "how much was taken": 3,
    "what happened at midnight": 3, "did you stay inside after that": 3,
    "what did you do next": 3, "who saw you": 3,
    # Confession
    "confess": 3, "tell me the truth": 3, "what are you hiding": 3,
    "reveal the truth": 3, "tell me what you know": 3,
    # Character identity (Tier 3 in dataset — reveals backstory/true motives)
    "who are you": 3, "your name": 3, "what do you do": 3,
    "what is your duty": 3, "what is your job": 3,
}

FOLLOWUP_PATTERNS = re.compile(
    r"\b(who|someone who|who was it|tell me more|what else|are you sure|can anyone vouch|"
    r"did you see|and then|what next|explain|elaborate|did you really|is that so|"
    r"i didn'?t get|what are you saying|what\?|huh\?|pardon|repeat that|really)\b",
    re.IGNORECASE
)


class DialogueState:
    def __init__(self):
        self.current_topic = "GREETING"
        self.current_depth = 0
        self.current_tier = 1

    def reset(self):
        self.current_topic = "GREETING"
        self.current_depth = 0
        self.current_tier = 1

    def process(self, raw_text: str, npc: str = "SHOPKEEPER") -> str:
        text = raw_text.strip().lower()
        clean = re.sub(r"[^\w\s]", " ", text)
        clean = " ".join(clean.split())

        # Direct navigation tags
        raw_upper = raw_text.strip().upper()
        if raw_upper in ["FIND_GUARD", "FIND_FARMER", "FIND_SHOPKEEPER", "FIND_KID", "FIND_OLD_MAN"]:
            return raw_upper

        # In-game navigation inquiries (Where is Guard / Farmer / Shopkeeper)
        if re.search(r"\b(where.*(find|is|are).*(guard|officer|gaurd)|where is the guard|find the guard|find the gaurd|where is guard)\b", clean):
            return "FIND_GUARD"
        if re.search(r"\b(where.*(find|is).*(farmer)|where is the farmer|find the farmer)\b", clean):
            return "FIND_FARMER"
        if re.search(r"\b(where.*(find|is).*(shopkeeper)|where is the shopkeeper|find the shopkeeper)\b", clean):
            return "FIND_SHOPKEEPER"
        if re.search(r"\b(where.*(find|is).*(kid|boy|child)|where is the kid|find the kid)\b", clean):
            return "FIND_KID"
        if re.search(r"\b(where.*(find|is).*(old man|elder)|where is the old man|find the old man)\b", clean):
            return "FIND_OLD_MAN"

        # Spiked drink / dizziness inquiry (Guard Tier 3 clue)
        if re.search(r"\b(dizzy|spiked|drink spiked|cider|drugged|passed out)\b", clean):
            self.current_topic = "PATROL"
            self.current_depth = 2
            self.current_tier = 3
            return "why were you dizzy"

        # Physical evidence / Key / Stash locations (Tier 3 Clue across all NPCs)
        if re.search(r"\b(physical evidence|evidence hidden|where is the key|where is the evidence|where.*key.*hidden|hidden in.*cane)\b", clean):
            self.current_topic = "CLUES"
            self.current_depth = 2
            self.current_tier = 3
            return "where is the key"

        # Duplicate key inquiry / Missing key (Guard Tier 3 clue)
        if re.search(r"\b(duplicate key|safe in your desk|who stole the key|key safe|duplicate vault key|did someone steal the key|check the desk|is your key safe|checked your key|your key safe)\b", clean):
            self.current_topic = "KEYS"
            self.current_depth = 2
            self.current_tier = 3
            if npc == "GUARD":
                return "is the duplicate key safe"
            return "where is the key"

        # Key possession / Access / Desk / Keys (Tier 2 probe)
        if re.search(r"\b(who has the key|have your key|your key|key taken|taken from council|desk|drawer|leaning over|visited.*desk|near your desk|brass keys|key|keys)\b", clean):
            if npc == "GUARD":
                if self.current_topic == "KEYS" and self.current_depth >= 1:
                    self.current_depth = 2
                    self.current_tier = 3
                    return "is the duplicate key safe"
                self.current_topic = "KEYS"
                self.current_depth = 1
                self.current_tier = 2
                return "who has the key"
            self.current_topic = "KEYS"
            self.current_depth = 1
            self.current_tier = 2
            return "who has the key"

        # Who really did it / key thief (Old Man Tier 3 clue)
        if re.search(r"\b(who took the duplicate key|who really did it|took the gold|reveal the truth)\b", clean):
            self.current_topic = "KEYS"
            self.current_depth = 2
            self.current_tier = 3
            return "who really did it"

        # Cane / Bone Tip (Kid / Old Man Clue)
        if re.search(r"\b(cane|bone tip|walking cane|tip|whose cane)\b", clean):
            self.current_topic = "CLUES"
            self.current_depth = 1
            self.current_tier = 2
            return "whose cane"

        # Lock / Beeswax / Chisel marks
        if re.search(r"\b(beeswax|graphite|lock mechanism|pry marks|chisel|how did they enter)\b", clean):
            self.current_topic = "THEFT"
            self.current_depth = 1
            self.current_tier = 2
            return "how did they enter"

        # Greaves / Armor / Alley sounds
        if re.search(r"\b(greaves|armor|clanking|sounds in the alley|running down the alley)\b", clean):
            self.current_topic = "SIGHTINGS"
            self.current_depth = 1
            self.current_tier = 2
            return "did you hear anything"

        # Handcart / Barrow
        if re.search(r"\b(handcart|hand barrow|delivery handcart|barrow|wheel.*handcart)\b", clean):
            if npc == "SHOPKEEPER":
                self.current_topic = "ALIBI"
                self.current_depth = 0
                self.current_tier = 1
                return "where were you last night"
            self.current_topic = "CART"
            self.current_depth = 2
            self.current_tier = 3
            if npc == "KID":
                return "where are they hiding the loot"
            return "where did the wagon go"

        # Shadows and signals (Kid Tier 3 clue)
        if re.search(r"\b(who were the shadows|shadows|signal|shadows signal|amber lamp|amber oil lamp)\b", clean):
            self.current_topic = "SIGHTINGS"
            self.current_depth = 2
            self.current_tier = 3
            return "who were the shadows"

        # Loot / Treasure / Stash locations
        if re.search(r"\b(where is the loot|where is the treasure|where did they haul|where are they hiding|where is the stolen treasure|where did you hide the gold|where did you hide the stolen gold|where did you hide the loot|where is the gold hidden|where is the stolen gold|where did you put the gold|where did you hide)\b", clean):
            self.current_topic = "LOOT"
            self.current_depth = 2
            self.current_tier = 3
            if npc == "KID":
                return "where are they hiding the loot"
            if npc == "SHOPKEEPER":
                return "tell me the truth"
            return "where did the wagon go"

        # Cart ruts, tracks, and direction of travel
        if re.search(r"\b(tracks|wheel ruts|cart ruts|wagon tracks|cart tracks|ruts|which way did (the|they|it)|where did the (cart|wagon|tracks) go|which way did the tracks lead|follow.*tracks)\b", clean):
            self.current_topic = "CART"
            if npc == "FARMER":
                self.current_depth = 2
                self.current_tier = 3
                return "where did the wagon go"
            elif npc == "KID":
                self.current_depth = 2
                self.current_tier = 3
                return "where are they hiding the loot"
            elif npc == "OLD_MAN":
                self.current_depth = 1
                self.current_tier = 2
                return "what did you see"
            else:
                self.current_depth = 2
                self.current_tier = 3
                return "where did the wagon go"

        # Vault Contents / Stolen Items / Amount Stolen (Tier 3)
        if re.search(r"\b(what was in the vault|what was stolen|how much was taken|what did (they|the thief) take|what was taken|how much gold|how much silver|how much was in)\b", clean):
            self.current_topic = "THEFT"
            self.current_depth = 2
            self.current_tier = 3
            if npc in ["SHOPKEEPER", "GUARD"]:
                return "what was in the vault"
            return "what happened last night"

        # Wearing / Appearance / Description
        if re.search(r"\b(wearing|wear|coat|dressed|what did (they|he|the thief|the person|the buyer) look like|see (their|his) face|recognize)\b", clean):
            if npc == "SHOPKEEPER":
                self.current_topic = "SACKS"
                self.current_depth = 2
                self.current_tier = 3
                return "tell me about the buyer"
            if npc == "FARMER":
                self.current_topic = "CART"
                self.current_depth = 2
                self.current_tier = 3
                return "did you see who was driving"
            if npc == "KID":
                self.current_topic = "SIGHTINGS"
                self.current_depth = 2
                self.current_tier = 3
                return "who were the shadows"
            self.current_topic = "SIGHTINGS"
            self.current_depth = 1
            self.current_tier = 2
            return "did you see anything"

        # Sacks / Rope / Tarps / Purchases (Shopkeeper Tier 2 & 3 clues)
        if re.search(r"\b(tarpaulin|tarpaulins|tarp|nails|tell me about the buyer|buyer|who bought|who purchased|bought anything|buy anything|bought from|buy from|bought.*rope|bought.*sack|purchase|purchased|customer|sold anything|did you sell)\b", clean):
            self.current_topic = "SACKS"
            self.current_depth = 2
            self.current_tier = 3
            if re.search(r"\b(tell me about|who was the|look like|wearing|buyer|describe)\b", clean):
                return "tell me about the buyer"
            return "who bought the sack"

        if re.search(r"\b(heavy sacks|sack|rope|twine|did you sell)\b", clean):
            self.current_topic = "SACKS"
            self.current_depth = 2
            self.current_tier = 3
            return "who bought the sack"

        # Unusual supplies / whale oil
        if re.search(r"\b(unusual supplies|whale oil|parchment|supplies)\b", clean):
            self.current_topic = "SIGHTINGS"
            self.current_depth = 0
            self.current_tier = 1
            return "did you notice anything unusual"

        # Alley inquiries
        if re.search(r"\b(alley|in your alley|back alley)\b", clean):
            if npc == "SHOPKEEPER":
                self.current_topic = "ALIBI"
                self.current_depth = 0
                self.current_tier = 1
                return "where were you last night"

        # Cart / Wagon inquiries (Farmer)
        if re.search(r"\b(who was driving|who drove the cart|driving the cart)\b", clean):
            if npc == "FARMER":
                self.current_topic = "CART"
                self.current_depth = 2
                self.current_tier = 3
                return "did you see who was driving"
            else:
                self.current_topic = "SIGHTINGS"
                self.current_depth = 1
                self.current_tier = 2
                return "did you see anything"

        if re.search(r"\b(who took the cart|took the wagon|took your cart)\b", clean):
            self.current_topic = "CART"
            self.current_depth = 2
            self.current_tier = 3
            return "who took the cart"

        if re.search(r"\b(about that cart|is your wagon|wagon still in the barn|cart in the barn|wheel squeak|wheel squeaking|squeaky)\b", clean):
            self.current_topic = "CART"
            self.current_depth = 1
            self.current_tier = 2
            return "about that cart"

        # Sleep / Watch inquiries (Guard / Farmer Tier 2)
        if re.search(r"\b(fall asleep|sleeping|asleep|asleep the whole night|fell asleep|on your watch|asleep on your watch)\b", clean):
            self.current_topic = "ALIBI"
            self.current_depth = 1
            self.current_tier = 2
            if npc == "GUARD":
                return "did you fall asleep"
            return "were you asleep the whole night"

        # Alibi / Where were you
        if re.search(r"\b(stay inside after that|step outside|stay inside)\b", clean):
            self.current_topic = "ALIBI"
            self.current_depth = 2
            self.current_tier = 3
            return "did you stay inside after that"

        if re.search(r"\b(are you sure|can anyone vouch|alone)\b", clean):
            self.current_topic = "ALIBI"
            self.current_depth = 1
            self.current_tier = 2
            return "are you sure"

        if re.search(r"\b(where were you|what were you doing|your alibi|where was you|at the time of)\b", clean):
            if npc == "KID":
                self.current_topic = "SIGHTINGS"
                self.current_depth = 1
                self.current_tier = 2
                return "did you see anything last night"
            self.current_topic = "ALIBI"
            self.current_depth = 0
            self.current_tier = 1
            if npc == "GUARD":
                return "where were you during the robbery"
            return "where were you at the time of robbery"

        # Physical Evidence / Dropped Items / Receipts
        if re.search(r"\b(paper|receipt|written on the receipt|what did the paper say|what was on the paper)\b", clean):
            self.current_topic = "CLUES"
            self.current_depth = 1
            self.current_tier = 2
            return "what was on the paper"

        if re.search(r"\b(drop anything|dropped anything|cinnamon|dried cloves|find clues|any evidence|badge|emblem|insignia|straw|chaff|graveyard)\b", clean):
            self.current_topic = "CLUES"
            self.current_depth = 1
            self.current_tier = 2
            return "did they drop anything"

        # Tools (Farmer)
        if re.search(r"\b(tools|crowbar|wedges|splitting wedges|shed)\b", clean):
            self.current_topic = "TOOLS"
            self.current_depth = 0
            self.current_tier = 1
            return "did you lose any tools"

        # Accusations / Confessions
        if re.search(r"\b(confess|tell me the truth|who really organized|where is the loot hidden)\b", clean):
            self.current_topic = "ACCUSATION"
            self.current_depth = 2
            self.current_tier = 3
            return "tell me the truth"

        if re.search(r"\b(did you steal|are you the thief|did you do it|you stole it|you look guilty)\b", clean):
            self.current_topic = "ACCUSATION"
            self.current_depth = 0
            self.current_tier = 1
            return "did you steal it"

        # Suspects / Who did it / Motive
        if re.search(r"\b(who did it|who is the thief|who is it|who was it|who do you suspect|do you know who|know who|anyone who|who broke into|suspect|might be the robber|who is the robber|motive|who had a motive|who took it|who could it be)\b", clean):
            if self.current_topic == "SUSPECTS":
                self.current_depth = min(self.current_depth + 1, 2)
            else:
                self.current_topic = "SUSPECTS"
                self.current_depth = 0

            npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["SHOPKEEPER"])
            tier_list = npc_topics.get("SUSPECTS", ["who do you suspect", "tell me who you suspect", "who had a motive"])
            res = tier_list[min(self.current_depth, len(tier_list) - 1)]
            self.current_tier = self.current_depth + 1
            return res

        # Theft / Incident / Vault
        if re.search(r"\b(what happened|tell me what happened|happened|robbery|theft|stole|incident|what occurred|break in|vault|treasury|about the vault|regarding the vault|at the vault)\b", clean):
            self.current_topic = "THEFT"
            self.current_depth = 0
            self.current_tier = 1
            return "what happened last night"

        # Sightings & Sounds
        if re.search(r"\b(see anyone|saw anyone|did you see anyone|did you see|see someone else|someone else|see anyone else|see anything|notice anything|see someone|saw something|hear anything|footsteps|noises)\b", clean):
            self.current_topic = "SIGHTINGS"
            self.current_depth = 1
            self.current_tier = 2
            if npc == "SHOPKEEPER":
                return "did you notice anything unusual"
            if npc == "FARMER":
                return "did you hear anything"
            if npc == "KID":
                return "did you see anything last night"
            return "what did you see"

        # Greetings
        if re.search(r"\b(hi|hello|hey|greetings|good day|howdy|halt)\b", clean):
            self.current_topic = "GREETING"
            self.current_depth = 0
            self.current_tier = 1
            return "hi"

        # Business / Harvest / Small talk (strictly non-purchasing)
        if re.search(r"\b(how is business|how are things with business|how is the harvest|how are the crops|how goes farming)\b", clean):
            self.current_topic = "GREETING"
            self.current_depth = 1
            self.current_tier = 2
            if npc == "FARMER":
                return "how is the harvest"
            return "how is business"

        if re.search(r"\b(who are you|your name|what do you do|what is your job|who are you exactly)\b", clean):
            self.current_tier = 2
            return "who are you"

        # Check for follow-up triggers on the active topic (NPC-aware lookup)
        if FOLLOWUP_PATTERNS.search(clean) or len(clean.split()) <= 2:
            if self.current_topic == "GREETING":
                # Advance from initial greeting into core theft / alibi investigation
                self.current_topic = "THEFT"
                self.current_depth = 0
            else:
                self.current_depth = min(self.current_depth + 1, 2)
            npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["SHOPKEEPER"])
            tier_list = npc_topics.get(self.current_topic, npc_topics.get("THEFT", ["what happened last night", "are you sure", "tell me the truth"]))
            res = tier_list[min(self.current_depth, len(tier_list) - 1)]
            self.current_tier = QUERY_TO_TIER.get(res, self.current_depth + 1)
            return res

        # Semantic Fallback: Map unrecognized queries to closest canonical training prompt
        # to ensure nanoGPT never receives out-of-distribution text that causes token glitches
        # Polite acknowledgments / Conversational transitions ("i see thanks", "got it", "thank you")
        if re.search(r"^(i see|thanks|thank you|ok|okay|got it|understood|alright)(\s+(thanks|thank you|sir|bro|officer))?[\.\!\?]?$", clean):
            self.current_depth = min(self.current_depth + 1, 2)
            npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["GUARD"])
            tier_list = npc_topics.get(self.current_topic, npc_topics.get("THEFT", npc_topics.get("ALIBI", ["what happened last night"])))
            res = tier_list[min(self.current_depth, len(tier_list) - 1)]
            self.current_tier = self.current_depth + 1
            return res

        if clean in QUERY_TO_TIER:
            self.current_tier = QUERY_TO_TIER[clean]
            return clean

        if re.search(r"\b(vault|gold|silver|stolen|theft|robbery|break|occurred|happened|treasure|mystery|crime|case|that happened|know anything|anything about|about that|about it)\b", clean):
            self.current_topic = "THEFT"
            self.current_depth = 0
            self.current_tier = 1
            return "what happened last night"
        elif re.search(r"\b(who|someone|anyone|suspect|thief|robber|guilty|blame|did it)\b", clean):
            self.current_topic = "SUSPECTS"
            self.current_depth = 0
            self.current_tier = 1
            return "who do you suspect"
        elif re.search(r"\b(saw|seeing|look|sight|shadow|lantern|light|sound|hear|did you see|anything outside)\b", clean):
            self.current_topic = "SIGHTINGS"
            self.current_depth = 1
            self.current_tier = 2
            return "what did you see"
        elif re.search(r"\b(where were you|what was your alibi|your alibi|where was you|were you asleep|were you sleeping|at home last night)\b", clean):
            if npc == "KID":
                self.current_topic = "SIGHTINGS"
                self.current_depth = 1
                self.current_tier = 2
                return "did you see anything last night"
            self.current_topic = "ALIBI"
            self.current_depth = 0
            self.current_tier = 1
            return "where were you last night"

        # Default fallback to active topic prompt (strictly within the target NPC's repertoire)
        npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["GUARD"])
        tier_list = npc_topics.get(self.current_topic, None)
        if not tier_list:
            tier_list = npc_topics.get("THEFT", npc_topics.get("ALIBI", ["hi"]))
        res = tier_list[min(self.current_depth, len(tier_list) - 1)]
        self.current_tier = self.current_depth + 1
        return res


dialogue_state = DialogueState()


def normalize_input(raw_text: str, npc: str = "SHOPKEEPER") -> str:
    return dialogue_state.process(raw_text, npc=npc)
