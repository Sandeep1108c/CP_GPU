"""
Stateful Multi-Tier Intent Matcher for nanoGPT Game Dialogue.
Tracks dialogue topic, depth, and tier (Tier 1 -> Tier 2 -> Tier 3) across successive turns,
allowing NPCs to reveal deeper clues and alibi details when pressed by the player.
Strictly NPC-aware and aligned 1:1 with the 34 canonical intents in SCENARIOS.
"""

import re
import os
import sys

# Load scenario dataset for dynamic scenario-aware tier & response resolution
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


def get_scenario_expected_response(culprit: str, npc: str, query: str):
    """Returns the canonical dataset response for (culprit, npc, query) if matched."""
    q_clean = query.lower().strip()
    entries = SCENARIOS.get(culprit, {}).get(npc, [])
    for tier, qs, resp in entries:
        for pattern in qs:
            if pattern.lower() == q_clean:
                return resp
    for tier, qs, resp in entries:
        for pattern in qs:
            if pattern.lower() in q_clean or q_clean in pattern.lower():
                return resp
    return None


# NPC-specific topic progression tiers for follow-up probing ("and then?", "tell me more", "are you sure?", etc.)
NPC_TOPIC_TIERS = {
    "SHOPKEEPER": {
        "ALIBI": ["where were you", "are you sure", "did you stay inside after that"],
        "SACKS": ["who bought the sack", "tell me about the buyer", "confess"],
        "SIGHTINGS": ["did you see anything", "what did you see", "who were the shadows"],
        "THEFT": ["what happened last night", "how did they enter", "what was in the vault"],
        "CLUES": ["did they drop anything", "what was on the paper", "where is the key"],
        "SUSPECTS": ["who do you suspect", "who had a motive", "who is the prime suspect"],
        "ACCUSATION": ["did you steal it", "you are lying", "confess"],
        "LOOT": ["about that cart", "did you see who was driving", "where is the loot"],
        "GREETING": ["hi", "how are you", "who are you"],
    },
    "GUARD": {
        "ALIBI": ["where were you", "did you fall asleep", "why were you dizzy"],
        "PATROL": ["how goes the patrol", "did you fall asleep", "why were you dizzy"],
        "KEYS": ["who has the key", "is the duplicate key safe", "where is the key"],
        "THEFT": ["what happened last night", "how did they enter", "what was in the vault"],
        "SIGHTINGS": ["did you see anything", "what did you see", "who were the shadows"],
        "CLUES": ["did they drop anything", "what was on the paper", "where is the key"],
        "SUSPECTS": ["who do you suspect", "who had a motive", "who is the prime suspect"],
        "ACCUSATION": ["did you steal it", "you are lying", "confess"],
        "LOOT": ["about that cart", "is the duplicate key safe", "where is the loot"],
        "GREETING": ["hi", "how are you", "who are you"],
    },
    "FARMER": {
        "ALIBI": ["where were you", "are you sure", "what happened at midnight"],
        "TOOLS": ["did you lose any tools", "about that cart", "where is the loot"],
        "CART": ["about that cart", "did you see who was driving", "where is the loot"],
        "LOOT": ["about that cart", "did you see who was driving", "where is the loot"],
        "THEFT": ["what happened last night", "how did they enter", "what was in the vault"],
        "SIGHTINGS": ["did you see anything", "what did you see", "who were the shadows"],
        "CLUES": ["did they drop anything", "what was on the paper", "where is the key"],
        "SUSPECTS": ["who do you suspect", "who had a motive", "who is the prime suspect"],
        "ACCUSATION": ["did you steal it", "you are lying", "confess"],
        "GREETING": ["hi", "how is the harvest", "who are you"],
    },
    "KID": {
        "SIGHTINGS": ["did you see anything", "what did you see", "who were the shadows"],
        "CLUES": ["did they drop anything", "what was on the paper", "where is the loot"],
        "THEFT": ["what happened last night", "how did they enter", "what was in the vault"],
        "ALIBI": ["where were you", "are you sure", "what happened at midnight"],
        "KEYS": ["who has the key", "whose cane", "where is the key"],
        "SUSPECTS": ["who do you suspect", "who had a motive", "who is the prime suspect"],
        "LOOT": ["what was on the paper", "who were the shadows", "where is the loot"],
        "GREETING": ["hi", "what are you doing", "who are you"],
    },
    "OLD_MAN": {
        "SIGHTINGS": ["did you see anything", "what did you see", "who were the shadows"],
        "THEFT": ["what happened last night", "how did they enter", "what was in the vault"],
        "ALIBI": ["where were you", "are you sure", "what happened at midnight"],
        "CLUES": ["did they drop anything", "whose cane", "where is the key"],
        "KEYS": ["who has the key", "whose cane", "where is the key"],
        "SUSPECTS": ["who do you suspect", "who had a motive", "who is the prime suspect"],
        "ACCUSATION": ["did you steal it", "you are lying", "confess"],
        "LOOT": ["what did you see", "where is the key", "where is the loot"],
        "GREETING": ["hi", "how are you", "who are you"],
    },
}

QUERY_TO_TIER = {
    # Tier 1
    "hi": 1, "hello": 1, "hey": 1, "greetings": 1, "good day": 1, "halt": 1, "officer": 1,
    "hey guard": 1, "hey farmer": 1, "hey kid": 1, "hey there": 1,
    "goodbye": 1, "bye": 1, "thanks": 1, "thank you": 1,
    "what happened": 1, "what happened last night": 1, "tell me what happened": 1,
    "tell me about the robbery": 1, "there was a robbery": 1,
    "where were you": 1, "where were you last night": 1, "where were you during the robbery": 1,
    "where were you at the time of robbery": 1, "what is your alibi": 1,
    "did you lose any tools": 1, "are your tools missing": 1, "what tools did you lose": 1,
    "did you see anything": 1, "did you hear anything": 1, "did you notice anything unusual": 1,
    "did they drop anything": 1, "did you find clues": 1, "any evidence": 1,
    "who do you suspect": 1, "who did it": 1, "who is the thief": 1, "any idea who is it": 1,
    "did you steal it": 1, "are you the thief": 1, "did you do it": 1, "you stole it": 1, "you look guilty": 1,

    # Tier 2
    "how are you": 2, "how are things": 2, "how is business": 2, "how is the harvest": 2,
    "how goes the patrol": 2, "what are you doing": 2,
    "how did they enter": 2, "how did they get in": 2, "was the door broken": 2, "did they pick the lock": 2,
    "are you sure": 2, "were you alone": 2, "can anyone vouch for you": 2, "did you step outside": 2,
    "did you fall asleep": 2, "were you sleeping": 2, "were you asleep the whole night": 2,
    "you fell asleep": 2, "be honest about your watch": 2,
    "what did you see": 2, "did you see anything last night": 2, "did you see anyone": 2,
    "what kind of sounds": 2, "did you hear footsteps": 2, "did you see lights": 2,
    "what was on the paper": 2, "show me the paper": 2, "what did the paper say": 2,
    "who has the key": 2, "who was near your desk": 2, "who visited the guard house": 2, "who had access": 2,
    "who bought the sack": 2, "did anyone buy unusual supplies": 2, "did you sell any heavy sacks": 2,
    "about that cart": 2, "is your cart in the barn": 2, "did someone take your cart": 2,
    "whose cane": 2, "what about the cane": 2,
    "who had a motive": 2, "tell me who you suspect": 2, "who was acting suspicious": 2,
    "what do you think of the others": 2, "tell me about the villagers": 2,
    "you are lying": 2, "you have a motive": 2, "your shop has debts": 2, "your gambling debts": 2,
    "you were seen near the vault": 2,

    # Tier 3
    "who are you": 3, "what do you do": 3, "your name": 3, "what is your story": 3,
    "what is your duty": 3, "what is your job": 3,
    "what was in the vault": 3, "what was stolen": 3, "how much was taken": 3,
    "did you stay inside after that": 3, "what happened at midnight": 3, "did you check the barn": 3,
    "what did you do next": 3, "who saw you": 3,
    "who were the shadows": 3, "did you see their faces": 3, "who was whistling": 3, "did you see shadows": 3,
    "is the duplicate key safe": 3, "check the desk": 3, "did someone steal the key": 3,
    "where is the key": 3, "where is the evidence hidden": 3, "where is the physical evidence hidden": 3,
    "who took the duplicate key": 3,
    "why were you dizzy": 3, "was your drink spiked": 3, "did someone drug you": 3,
    "tell me about the buyer": 3, "who bought the rope": 3, "what was the buyer wearing": 3,
    "did you see who was driving": 3, "who took the cart": 3,
    "who is the prime suspect": 3, "who really did it": 3, "tell me who you think took it": 3,
    "tell me what you know": 3, "reveal the truth": 3, "name names": 3, "tell me more": 3,
    "confess": 3, "tell me the truth": 3, "what are you hiding": 3, "who really organized this theft": 3,
    "where is the loot": 3, "where did the wagon go": 3, "where are they hiding the loot": 3,
    "where did the cart go": 3, "where were they pushing the hand-barrow": 3,
}

FOLLOWUP_PATTERNS = re.compile(
    r"^(who|someone who|who was it|tell me more|what else|and then|and then what happened|"
    r"what happened next|what next|explain|elaborate|did you really|is that so|"
    r"i didn'?t get|what are you saying|what|huh|pardon|repeat that|really|why|how|when|where)$",
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

    def _set_state(self, topic: str, tier: int, canonical: str) -> str:
        self.current_topic = topic
        self.current_tier = tier
        self.current_depth = max(0, tier - 1)
        return canonical

    def process(self, raw_text: str, npc: str = "SHOPKEEPER") -> str:
        raw_upper = raw_text.strip().upper()
        if raw_upper in ["FIND_GUARD", "FIND_FARMER", "FIND_SHOPKEEPER", "FIND_KID", "FIND_OLD_MAN"]:
            return raw_upper

        text = raw_text.strip().lower()
        clean = re.sub(r"[^\w\s]", " ", text)
        clean = " ".join(clean.split())

        # 0. In-game navigation inquiries ("Where can I find the guard?", etc.)
        if re.search(r"^(where can i find|where is|where are|how do i find|find) (the )?(guard|officer|gaurd|escanor|captain escanor)$", clean):
            return "FIND_GUARD"
        if re.search(r"^(where can i find|where is|where are|how do i find|find) (the )?(farmer|zoro|roronoa zoro)$", clean):
            return "FIND_FARMER"
        if re.search(r"^(where can i find|where is|where are|how do i find|find) (the )?(shopkeeper|merchant|dazai|dazai osamu)$", clean):
            return "FIND_SHOPKEEPER"
        if re.search(r"^(where can i find|where is|where are|how do i find|find) (the )?(kid|boy|child|naruto|naruto uzumaki)$", clean):
            return "FIND_KID"
        if re.search(r"^(where can i find|where is|where are|how do i find|find) (the )?(old man|elder|roshi|master roshi|corvus)$", clean):
            return "FIND_OLD_MAN"

        # 1. Exact canonical match check (prevents double-normalization drift)
        if clean in QUERY_TO_TIER and not FOLLOWUP_PATTERNS.match(clean):
            tier = QUERY_TO_TIER[clean]
            self.current_tier = tier
            self.current_depth = max(0, tier - 1)
            return clean

        # 2. Pure short follow-up triggers ("and then?", "what else?", "tell me more", "why?", "really?")
        if FOLLOWUP_PATTERNS.match(clean):
            if self.current_topic == "GREETING":
                self.current_topic = "THEFT"
                self.current_depth = 0
            else:
                self.current_depth = min(self.current_depth + 1, 2)
            npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["SHOPKEEPER"])
            tier_list = npc_topics.get(self.current_topic, ["what happened last night", "how did they enter", "what was in the vault"])
            res = tier_list[min(self.current_depth, len(tier_list) - 1)]
            self.current_tier = QUERY_TO_TIER.get(res, self.current_depth + 1)
            return res

        # 3. Spiked drink / dizziness / poison / cider flask inspection (Tier 3)
        if re.search(r"\b(dizzy|spiked|drink spiked|cider|flask|drugged|poison|poisoned|passed out|fainted)\b", clean):
            return self._set_state("PATROL", 3, "why were you dizzy")

        # 4. Physical evidence / Key hiding spot / Rainwater barrel inspection (Tier 3)
        if re.search(r"\b(physical evidence|evidence hidden|where is the key|where is the missing.*key|where.*key.*hidden|hidden in.*cane|what is hidden in.*cane|unscrew.*cane|skeleton key|rainwater barrel|inspect.*barrel|check.*barrel|inside.*barrel)\b", clean):
            return self._set_state("KEYS", 3, "where is the key")

        # 5. Cane / Bone tip inquiry (Tier 2)
        if re.search(r"\b(cane|bone tip|walking cane|whose cane|missing its.*tip)\b", clean):
            return self._set_state("CLUES", 2, "whose cane")

        # 6. Duplicate key safety / Stolen key from desk drawer (Tier 3)
        if re.search(r"\b(duplicate.*key.*safe|safe in your desk|still in your desk|who stole the key|who took the duplicate key|did someone steal the key|check the desk|is your key safe|key from your drawer|stole the key)\b", clean):
            if npc == "GUARD":
                return self._set_state("KEYS", 3, "is the duplicate key safe")
            return self._set_state("KEYS", 3, "where is the key")

        # 7. Desk / Guardhouse visitors / Who has access to the key (Tier 2)
        if re.search(r"\b(who has.*key|access to.*key|near your desk|visited.*desk|visited.*guardhouse|visit.*guardhouse|guard house|who had access|desk drawer|banging his fists)\b", clean):
            return self._set_state("KEYS", 2, "who has the key")

        # 8. Lock / Entry mechanism / Beeswax / Chisel / Forced door / Blueprints (Tier 2)
        if re.search(r"\b(how did they (enter|get in|break in)|how was the lock|lock opened|pick the lock|lock picked|door forced|forced open|was the door broken|beeswax|graphite|pry marks|chisel|designed the vault|vault lock|know.*lock works)\b", clean):
            return self._set_state("THEFT", 2, "how did they enter")

        # 9. Vault contents / What was stolen / How much gold (Tier 3)
        if re.search(r"\b(what was in the vault|what was stolen|how much.*(taken|stolen|gold|silver)|what did (they|the thief) (take|steal)|what was taken)\b", clean):
            return self._set_state("THEFT", 3, "what was in the vault")

        # 10. Loot / Treasure / Cart destination / Hay bales / Crypt / Silo inspection (Tier 3)
        if re.search(r"\b(where is the (loot|treasure|gold|stolen)|where did (you|they) hide|where are they hiding|where did they haul|where did the (wagon|cart|squeaky cart|handcart|barrow) go|which way did the (cart|wagon|tracks)|where were they pushing|wheel the handcart|hay bales|search.*crypt|chapel crypt|grain silo|false floor)\b", clean):
            if npc == "KID":
                return self._set_state("LOOT", 3, "where are they hiding the loot")
            return self._set_state("LOOT", 3, "where is the loot")

        # 11. Sacks / Rope / Tarpaulins / Whale oil / Store buyer (Tier 2 & 3)
        if re.search(r"\b(tell me.*about.*buyer|what did the (customer|buyer).*look like|what was the buyer wearing|buyer wearing|describe the buyer)\b", clean):
            return self._set_state("SACKS", 3, "tell me about the buyer")

        if re.search(r"\b(sack|sacks|rope|hemp|tarpaulin|tarpaulins|tarp|horseshoe nails|whale oil|emery|unusual supplies|buy anything|bought anything|did you sell|who bought|customer)\b", clean):
            if re.search(r"\b(who bought|tell me about|buyer)\b", clean):
                return self._set_state("SACKS", 3, "tell me about the buyer")
            return self._set_state("SACKS", 2, "who bought the sack")

        # 12. Paper / Receipt / Dropped Clues / Evidence (Tier 1 & 2)
        if re.search(r"\b(paper|receipt|written on|smell like|cinnamon|cloves|iou|ious)\b", clean):
            return self._set_state("CLUES", 2, "what was on the paper")

        if re.search(r"\b(drop anything|dropped anything|find clues|find any clues|any clues|any evidence|clues in the|graveyard gravel|oat straw|chaff|river clay|eagle badge|bronze badge)\b", clean):
            return self._set_state("CLUES", 1, "did they drop anything")

        # 13. Tools / Crowbar / Shed (Tier 1)
        if re.search(r"\b(lose any tools|tools missing|what tools|tools|crowbar|splitting wedges|shed)\b", clean):
            return self._set_state("TOOLS", 1, "did you lose any tools")

        # 14. Cart / Wagon / Squeaky wheel / Who was driving (Tier 2 & 3)
        if re.search(r"\b(who was driving|who drove|driving the (cart|wagon)|who took the (cart|wagon))\b", clean):
            return self._set_state("CART", 3, "did you see who was driving")

        if re.search(r"\b(about that cart|happened to your cart|cart in the barn|wagon.*in the barn|take your cart|wheel squeak|squeaking|squeaky|handcart|hand barrow|barrow|wheel ruts|wagon tracks)\b", clean):
            return self._set_state("CART", 2, "about that cart")

        # 15. Shadows / Whistle / Midnight / Barn check (Tier 3)
        if re.search(r"\b(who were the shadows|shadows|amber lamp|amber oil lamp|whistle|whistling|see their faces|running down the alley)\b", clean):
            return self._set_state("SIGHTINGS", 3, "who were the shadows")

        if re.search(r"\b(check the barn|at midnight|happened at midnight|stay inside after that|step outside into the lane)\b", clean):
            if npc == "SHOPKEEPER":
                return self._set_state("ALIBI", 3, "did you stay inside after that")
            return self._set_state("ALIBI", 3, "what happened at midnight")

        # 16. Sleep / Watch / Vouching / Alone (Tier 2)
        if re.search(r"\b(fall asleep|sleeping|asleep|fell asleep|on your watch|happened on your watch)\b", clean):
            return self._set_state("ALIBI", 2, "did you fall asleep")

        if re.search(r"\b(are you sure|vouch|confirm where you were|anyone confirm|were you alone|alone in your|step outside|check your alley|awake last night)\b", clean):
            return self._set_state("ALIBI", 2, "are you sure")

        # 17. Alibi / Where were you (Tier 1)
        if re.search(r"\b(where were you|what were you doing|your alibi|where was you|at the time of)\b", clean):
            return self._set_state("ALIBI", 1, "where were you")

        # 18. Confessions & Accusations (Tier 1, 2, 3)
        if re.search(r"\b(confess|tell me the truth|reveal the truth|who really organized|what are you hiding|admit it|staged the theft)\b", clean):
            return self._set_state("ACCUSATION", 3, "confess")

        if re.search(r"\b(you are lying|liar|your shop.*debt|gambling debt|dice debt|you have a motive|seen near the vault)\b", clean):
            return self._set_state("ACCUSATION", 2, "you are lying")

        if re.search(r"\b(did you steal|are you the thief|did you do it|you stole|you look guilty|did you rob)\b", clean):
            return self._set_state("ACCUSATION", 1, "did you steal it")

        # 19. Suspects / Motive / Specific NPC Mentions (Tier 1, 2, 3)
        if re.search(r"\b(prime suspect|who really did it|who took the gold|tell me who you think)\b", clean):
            return self._set_state("SUSPECTS", 3, "who is the prime suspect")

        if re.search(r"\b(motive|acting suspicious|why would (zoro|dazai|escanor|roshi|the farmer|the guard|the shopkeeper|the old man)|tell me who you suspect|name names)\b", clean):
            return self._set_state("SUSPECTS", 2, "who had a motive")

        if re.search(r"\b(what do you think of (the others|everyone|the villagers|dazai|escanor|zoro|naruto|roshi)|tell me about the villagers)\b", clean):
            return self._set_state("SUSPECTS", 2, "what do you think of the others")

        if re.search(r"\b(who do you (suspect|think)|who is the (thief|robber|culprit)|who did it|who is responsible|any idea who|who could have)\b", clean):
            return self._set_state("SUSPECTS", 1, "who do you suspect")

        # 20. Sightings & Sounds (Tier 1 & 2)
        if re.search(r"\b(what did you (see|hear)|tell me what you saw|scouting on the roofs|hear or see|see or hear|hear any noises|sounds in the alley|near the chapel|one in the morning|two in the morning)\b", clean):
            return self._set_state("SIGHTINGS", 2, "what did you see")

        if re.search(r"\b(did you (see|hear|notice)|anything unusual|anything strange|see anyone|saw anyone|footsteps|noises|lights)\b", clean):
            return self._set_state("SIGHTINGS", 1, "did you see anything")

        # 21. General Theft / What happened (Tier 1)
        if re.search(r"\b(what happened|tell me about the (robbery|theft|vault|crime|case)|there was a robbery|about the vault|vault door|council vault|hear about the robbery)\b", clean):
            return self._set_state("THEFT", 1, "what happened last night")

        # 22. Identity / Backstory / Status / Greetings / Farewells
        if re.search(r"\b(who are you|your name|what is your (story|job|duty)|what do you do here|tell me about yourself)\b", clean):
            return self._set_state("GREETING", 3, "who are you")

        if re.search(r"\b(how are you|how are things|how is (business|the harvest|farming)|how goes the patrol|what are you doing|brings peace)\b", clean):
            return self._set_state("GREETING", 2, "how are you")

        if re.search(r"\b(goodbye|bye|see ya|farewell|thanks|thank you)\b", clean):
            return self._set_state("GREETING", 1, "goodbye")

        if re.search(r"\b(hi|hello|hey|greetings|good day|good morning|good evening|howdy|halt|welcome|yo|sup)\b", clean):
            return self._set_state("GREETING", 1, "hi")

        # 23. Safe Contextual Fallback
        npc_topics = NPC_TOPIC_TIERS.get(npc, NPC_TOPIC_TIERS["SHOPKEEPER"])
        tier_list = npc_topics.get(self.current_topic, ["what happened last night", "how did they enter", "what was in the vault"])
        res = tier_list[min(self.current_depth, len(tier_list) - 1)]
        self.current_tier = QUERY_TO_TIER.get(res, 1)
        return res


dialogue_state = DialogueState()


def normalize_input(raw_text: str, npc: str = "SHOPKEEPER") -> str:
    return dialogue_state.process(raw_text, npc=npc)
