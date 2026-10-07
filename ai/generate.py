"""
Interactive NPC dialogue generation using trained multi-culprit nanoGPT model.

Usage:
    python ai/generate.py

Loads the best checkpoint and generates NPC responses given a prompt.
Supports specifying Active Culprit Scenario, NPC, trust level, mood, and memory context.
"""

import os
import sys
import random
import pickle

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import GPT, GPTConfig

# ============================================================
# Config
# ============================================================

ckpt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
device = "cuda" if torch.cuda.is_available() else "cpu"

# Generation params
temperature = 0.40        # keeps character identity razor-sharp and prevents role cross-talk
top_p = 0.80              # nucleus sampling (cuts off the bottom 20% probability tail)
top_k = None              # rely on dynamic top-p instead of rigid top-k
repetition_penalty = 1.25 # penalizes repeating tokens already generated
max_new_tokens = 70       # sufficient for 2-3 full sentence responses

# In-game NPC location guidance
NPC_LOCATIONS = {
    "FIND_GUARD": "Escanor is on duty at the north gate and watchpost by the treasury. (Tip: Type '/guard' to speak with him!)",
    "FIND_FARMER": "Zoro is out by his barn and farmhouse near the eastern fields. (Tip: Type '/farmer' to speak with him!)",
    "FIND_SHOPKEEPER": "Dazai is behind the counter inside the general dry goods store. (Tip: Type '/shopkeeper' to speak with him!)",
    "FIND_KID": "Naruto is training by the water well in the village square. (Tip: Type '/kid' to speak with him!)",
    "FIND_OLD_MAN": "Master Roshi is resting on his front porch overlooking the village lane. (Tip: Type '/old_man' to speak with him!)",
}

# ============================================================
# Load model
# ============================================================

def load_model():
    ckpt_path = os.path.join(ckpt_dir, "final.pt")
    if not os.path.exists(ckpt_path):
        ckpt_path = os.path.join(ckpt_dir, "best.pt")
    if not os.path.exists(ckpt_path):
        print("ERROR: No checkpoint found. Train the model first!")
        sys.exit(1)

    print(f"Loading checkpoint: {ckpt_path}")
    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)

    # Rebuild config
    cfg = checkpoint["config"]
    config = GPTConfig(
        vocab_size=cfg["vocab_size"],
        block_size=cfg["block_size"],
        n_layer=cfg["n_layer"],
        n_head=cfg["n_head"],
        n_embd=cfg["n_embd"],
    )

    model = GPT(config)
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    meta = checkpoint["meta"]
    return model, meta


def get_tokenizer():
    tok_path = os.path.join(data_dir, "bpe_tokenizer.pkl")
    if os.path.exists(tok_path):
        from tokenizer import BPETokenizer
        return BPETokenizer.load(tok_path)
    return None

tokenizer_instance = get_tokenizer()

def encode(s, stoi):
    if tokenizer_instance is not None:
        return tokenizer_instance.encode(s)
    return [stoi[c] for c in s if c in stoi]


def decode(l, itos):
    if tokenizer_instance is not None:
        return tokenizer_instance.decode(l)
    return "".join([itos[i] for i in l if i in itos])


def build_prompt(culprit, npc, trust, memory, mood, player_input):
    """Build a prompt in the multi-culprit training data format."""
    return f"<|culprit|>{culprit}<|npc|>{npc}<|trust|>{trust}<|memory|>{memory}<|mood|>{mood}<|input|>{player_input}<|response|>"


from intent import normalize_input, dialogue_state, QUERY_TO_TIER, get_scenario_query_tier


def generate_response(model, meta, npc, trust, memory, mood, player_input, culprit="SHOPKEEPER"):
    """Generate an NPC response with fuzzy intent normalization, tiered depth, and culprit conditioning."""
    if player_input in NPC_LOCATIONS:
        return NPC_LOCATIONS[player_input]

    stoi = meta["stoi"]
    itos = meta["itos"]

    # Normalize casual player phrasing with NPC awareness
    normalized_query = normalize_input(player_input, npc=npc)

    # Handle in-game navigation inquiries directly
    if normalized_query in NPC_LOCATIONS:
        return NPC_LOCATIONS[normalized_query]

    # Dynamic Scenario-Aware Tier Resolution: look up true tier for this (culprit, npc, query)
    if not memory or memory in ["none", "no memory", "null"] or not memory.startswith("tier"):
        query_tier = get_scenario_query_tier(culprit, npc, normalized_query)
        tier_memory = f"tier{query_tier}"
    else:
        tier_memory = memory

    # Ensure prompt trust aligns with training distribution for this query tier
    prompt_trust = trust
    if tier_memory == "tier3" and prompt_trust == "LOW":
        prompt_trust = "MEDIUM"
    elif tier_memory == "tier1" and prompt_trust == "HIGH":
        prompt_trust = "MEDIUM"

    prompt = build_prompt(culprit, npc, prompt_trust, tier_memory, mood, normalized_query)
    tokens = encode(prompt, stoi)
    x = torch.tensor(tokens, dtype=torch.long, device=device).unsqueeze(0)

    end_token_id = stoi.get("<|end|>", None)
    with torch.no_grad():
        y = model.generate(
            x,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            end_token_id=end_token_id
        )

    # Only take newly generated tokens after prompt
    new_tokens = y[0][len(tokens):].tolist()
    if end_token_id in new_tokens:
        end_idx = new_tokens.index(end_token_id)
        new_tokens = new_tokens[:end_idx]

    reply = decode(new_tokens, itos).strip()
    # Clean up any lingering tag artifacts if present
    if "<|" in reply:
        reply = reply.split("<|")[0].strip()
    if "|>" in reply:
        reply = reply.split("|>")[-1].strip()

    # Truncate trailing fragment after final complete punctuation
    last_punct = max(reply.rfind("."), reply.rfind("!"), reply.rfind("?"), reply.rfind("~"), reply.rfind('"'))
    if last_punct > 0:
        reply = reply[:last_punct + 1].strip()

    return reply


# ============================================================
# Interactive CLI
# ============================================================

NPCS = ["SHOPKEEPER", "GUARD", "FARMER", "KID", "OLD_MAN"]
CULPRITS = ["SHOPKEEPER", "FARMER", "GUARD", "OLD_MAN"]
TRUST_LEVELS = ["LOW", "MEDIUM", "HIGH"]
MOODS = ["friendly", "suspicious", "calm", "nervous", "defensive", "annoyed", "curious"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    model, meta = load_model()

    NPC_NAMES = {
        "SHOPKEEPER": "SHOPKEEPER (Dazai Osamu)",
        "GUARD": "GUARD (Escanor)",
        "FARMER": "FARMER (Roronoa Zoro)",
        "KID": "KID (Naruto Uzumaki)",
        "OLD_MAN": "OLD_MAN (Master Roshi)"
    }

    print("\n" + "=" * 75)
    print("NPC Interrogation Engine — Find the Thief")
    print("Detective: Lelouch vi Britannia (Zero)")
    print("Cast:      Dazai (Shopkeeper) | Escanor (Guard) | Zoro (Farmer)")
    print("           Naruto (Kid)        | Master Roshi (Old Man)")
    print("=" * 75)
    print("Available Suspects:  SHOPKEEPER, FARMER, GUARD, OLD_MAN")
    print("\nQuick Commands:")
    print("  Switch NPC:        /guard, /farmer, /shopkeeper, /kid, /old_man")
    print("  Set Culprit/Case:  /culprit <NAME> or /newgame (random culprit)")
    print("  Change Trust:      /low, /med, /high")
    print("  Help / Reset:      /help, /reset, quit")
    print("=" * 75 + "\n")

    # Default context & Per-NPC State
    culprit = "SHOPKEEPER"
    npc = "SHOPKEEPER"
    memory = "none"
    npc_trust = {n: "LOW" for n in NPCS}
    npc_turns = {n: 0 for n in NPCS}
    npc_mood = {n: "friendly" for n in NPCS}
    trust = npc_trust[npc]
    mood = npc_mood[npc]

    while True:
        # Show current context
        display_npc = NPC_NAMES.get(npc, npc)
        display_culprit = NPC_NAMES.get(culprit, culprit)
        turns_info = f"{npc_turns[npc]}/2 to MED" if trust == "LOW" else (f"{npc_turns[npc]}/4 to HIGH" if trust == "MEDIUM" else "MAX")
        print(f"[Case Culprit: {display_culprit} | Target: {display_npc} | Trust: {trust} ({turns_info}) | Mood: {mood}]")
        try:
            player_input = input("[Zero / Lelouch]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not player_input:
            continue

        cmd = player_input.lower().strip()
        if cmd == "quit":
            break

        if cmd in ["/help", "help", "/?"]:
            print("\n--- Command Guide ---")
            print("  Switch NPC:     /guard, /farmer, /shopkeeper, /kid, /old_man (or /npc <NAME>)")
            print("  Change Culprit: /culprit <SHOPKEEPER|FARMER|GUARD|OLD_MAN> (or /case <NAME>)")
            print("  New Mystery:    /newgame (picks a random culprit and resets trust!)")
            print("  Manual Trust:   /low, /med, /high (or /trust <LOW|MEDIUM|HIGH>)")
            print("  Manual Mood:    /mood <friendly|suspicious|calm|nervous|defensive>")
            print("  Reset Topic:    /reset")
            print("  Exit:           quit\n")
            continue

        if cmd in ["/newgame", "/random"]:
            culprit = random.choice(CULPRITS)
            for n in NPCS:
                npc_trust[n] = "LOW"
                npc_turns[n] = 0
                npc_mood[n] = "friendly"
            trust = "LOW"
            mood = "friendly"
            dialogue_state.reset()
            print(f"\n  *** NEW MYSTERY STARTED! A random culprit has been selected for this case. ***")
            print(f"  (Developer Reveal: The secret culprit for this case is {culprit})\n")
            continue

        if cmd.startswith("/culprit ") or cmd.startswith("/case "):
            chosen = player_input.split(maxsplit=1)[1].strip().upper()
            if chosen in CULPRITS:
                culprit = chosen
                for n in NPCS:
                    npc_trust[n] = "LOW"
                    npc_turns[n] = 0
                    npc_mood[n] = "friendly"
                trust = "LOW"
                mood = "friendly"
                dialogue_state.reset()
                print(f"  -> Mystery case culprit set to: {culprit} (All NPC trust & moods reset)\n")
            else:
                print(f"  Unknown culprit. Choose from: {', '.join(CULPRITS)}\n")
            continue

        if cmd in ["/guard", "/farmer", "/shopkeeper", "/kid", "/old_man", "/oldman"]:
            npc = cmd.lstrip("/").upper()
            if npc == "OLDMAN":
                npc = "OLD_MAN"
            trust = npc_trust[npc]
            mood = npc_mood[npc]
            dialogue_state.reset()
            print(f"  -> Switched to {npc} (Trust: {trust} | Mood: {mood})\n")
            continue

        if player_input.startswith("/npc "):
            npc = player_input[5:].strip().upper()
            if npc in NPCS:
                trust = npc_trust[npc]
                mood = npc_mood[npc]
                dialogue_state.reset()
                print(f"  -> Switched to {npc} (Trust: {trust} | Mood: {mood})\n")
            else:
                print(f"  Unknown NPC. Choose from: {', '.join(NPCS)}\n")
            continue

        if cmd in ["/low", "/med", "/medium", "/high"]:
            trust = "LOW" if cmd == "/low" else ("MEDIUM" if cmd in ["/med", "/medium"] else "HIGH")
            npc_trust[npc] = trust
            npc_turns[npc] = 0 if trust == "LOW" else (2 if trust == "MEDIUM" else 4)
            print(f"  -> {npc}'s Trust set to {trust}\n")
            continue

        if player_input.startswith("/trust "):
            t_val = player_input[7:].strip().upper()
            if t_val in TRUST_LEVELS:
                trust = t_val
                npc_trust[npc] = trust
                npc_turns[npc] = 0 if trust == "LOW" else (2 if trust == "MEDIUM" else 4)
                print(f"  -> {npc}'s Trust set to {trust}\n")
            else:
                print(f"  Unknown trust level. Choose from: {', '.join(TRUST_LEVELS)}\n")
            continue

        if player_input.startswith("/mood "):
            m_val = player_input[6:].strip().lower()
            if m_val in MOODS:
                mood = m_val
                npc_mood[npc] = mood
                print(f"  -> {npc}'s Mood set to {mood}\n")
            else:
                print(f"  Unknown mood. Choose from: {', '.join(MOODS)}\n")
            continue

        if player_input.startswith("/memory "):
            memory = player_input[8:].strip()
            print(f"  -> Memory set to: {memory}\n")
            continue

        if cmd == "/reset":
            dialogue_state.reset()
            npc_turns[npc] = 0
            npc_trust[npc] = "LOW"
            npc_mood[npc] = "friendly"
            trust = "LOW"
            mood = "friendly"
            print("  -> Dialogue state, trust, and mood reset to beginning.\n")
            continue

        # Dynamic Mood Modulation based on tone and accusation
        lower_in = player_input.lower()
        if any(w in lower_in for w in ["you stole", "are you the thief", "you did it", "liar", "confess", "guilty", "suspect you", "accuse"]):
            new_mood = "nervous" if npc == culprit else "defensive"
        elif any(w in lower_in for w in ["hi", "hello", "good day", "greetings", "thanks", "thank you", "please"]):
            new_mood = "friendly"
        elif any(w in lower_in for w in ["are you sure", "were you alone", "can anyone vouch", "why were you"]):
            new_mood = "suspicious" if trust == "LOW" else "calm"
        else:
            new_mood = mood

        if new_mood != mood:
            mood = new_mood
            npc_mood[npc] = mood
            print(f"  ⚡ [{display_npc}'s mood shifted to: {mood.upper()}]")

        # Generate response
        response = generate_response(model, meta, npc, trust, memory, mood, player_input, culprit=culprit)
        print(f"{npc}: {response}\n")

        # Dynamic Trust Progression
        npc_turns[npc] += 1
        if any(clue in lower_in for clue in ["spiked", "dizzy", "cider", "crowbar", "receipt", "sacks", "wheel", "ruts", "greaves", "chisel", "eagle", "cane", "beeswax", "skeleton key"]):
            npc_turns[npc] = max(npc_turns[npc], 2)

        old_trust = npc_trust[npc]
        if npc_turns[npc] >= 4 and old_trust != "HIGH":
            npc_trust[npc] = "HIGH"
            trust = "HIGH"
            print(f"  ✨ [{display_npc}'s trust in Detective Zero has reached HIGH! Deep secrets & confessions unlocked.]\n")
        elif npc_turns[npc] >= 2 and old_trust == "LOW":
            npc_trust[npc] = "MEDIUM"
            trust = "MEDIUM"
            print(f"  ✨ [{display_npc}'s trust in Detective Zero has grown to MEDIUM! Deeper alibis & clues unlocked.]\n")


if __name__ == "__main__":
    main()
