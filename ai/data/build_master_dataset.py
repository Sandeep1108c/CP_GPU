"""
Master Multi-Tier Dataset Generator for 'Find the Thief' RPG Console.
Builds 3 progressive depth tiers (Tier 1: Initial, Tier 2: Probing, Tier 3: Revelation)
across all core topics for all 5 NPCs, with varied player inquiry styles.
Keeps parameter count at exactly 4.79M (< 5.0M) while giving deep dynamic conversations.
"""

import os

OUTPUT_FILE = r"D:\CP GPU\ai\data\training_data_master.txt"
BASE_FILE = r"C:\Users\sande\Downloads\training_data.txt"

with open(BASE_FILE, "r", encoding="utf-8") as f:
    base_lines = [l.strip() for l in f.readlines() if l.strip()]

print(f"Loaded {len(base_lines)} base training samples.")

# Progressive 3-Tier Topic Structure
# (Topic, Tier, Player Queries List, NPC Response)

MULTI_TIER_DIALOGUES = {
    "SHOPKEEPER": [
        # --- GREETINGS ---
        (1, ["hi", "hello", "hey", "greetings", "good day"],
         "Welcome to my shop. Dry goods, cloth, tools, seeds. Let me know what you need."),
        (2, ["how are you", "how are things", "how is business"],
         "Business is tense today. Ever since the theft last night, everyone is eyeing their neighbors with suspicion."),
        (3, ["who are you", "what do you do", "your name"],
         "I am the village shopkeeper. I have run this general store for twenty years."),

        # --- ALIBI TOPIC ---
        (1, ["where were you", "where were you last night", "what were you doing at the time of robbery", "what is your alibi"],
         "I was inside my shop the entire evening doing the month's accounting ledger. I live right behind the counter."),
        (2, ["are you sure", "were you alone", "can anyone vouch for you", "did you step outside"],
         "I live alone, but I did step out around the tenth hour to bring in a storage crate from the lane."),
        (3, ["did you stay inside after that", "what did you do next", "who saw you"],
         "I locked the front bolt firmly. When I was locking up, I heard footsteps moving quickly toward the eastern lane."),

        # --- THEFT TOPIC ---
        (1, ["what happened", "what happened last night", "there was a robbery", "tell me what happened", "tell me about the robbery"],
         "Someone broke into the council vault near the eastern lane last night. Valuables were taken. That is all I know."),
        (2, ["how did they get in", "was the door broken", "did they pick the lock", "who has the key"],
         "Between us, the vault lock was not forced. Whoever took the gold either had a key or knew the combination mechanism."),
        (3, ["what was in the vault", "what was stolen", "how much was taken"],
         "The council tax treasury—heavy sacks of silver and gold coins, along with important land deeds."),

        # --- SUSPECTS TOPIC ---
        (1, ["who did it", "who is the thief", "who do you suspect", "any idea who is it", "who could have done it"],
         "I am not in the habit of pointing fingers at my neighbors without proof. You should ask the guard."),
        (2, ["someone who", "who was acting suspicious", "name names", "tell me who you suspect", "who had a motive"],
         "The farmer lost tools recently and has been bitter about the council taxes. And someone bought a heavy canvas sack from me yesterday."),
        (3, ["who bought the sack", "tell me about the buyer", "who bought the rope"],
         "A customer in a hooded work coat bought an oversized sack and fifteen paces of thick hemp rope yesterday. Paid exact silver and walked with a farmer's heavy gait."),

        # --- SIGHTINGS & SOUNDS ---
        (1, ["did you see anything", "did you hear anything", "did you notice anything unusual"],
         "I heard only the wind and regular nighttime sounds. My shutters were closed before dark."),
        (2, ["what kind of sounds", "did you hear footsteps", "did you hear noises", "tell me more"],
         "Now that you press me, I heard a low bird whistle from the vault path around midnight, followed by an answering call from near the mill."),
        (3, ["who was whistling", "what happened after the whistle", "did you see shadows"],
         "I peeked through the shutter slat and saw two figures moving a heavy bundle toward the old mill road cart."),

        # --- ACCUSATIONS ---
        (1, ["did you steal it", "are you the thief", "did you do it", "you stole it", "you look guilty"],
         "What an outrageous accusation! I run an honest business. Take your wild guesses elsewhere."),
        (2, ["you have a motive", "your shop has debts", "you were seen near the vault"],
         "Every shop has seasonal expenses! That does not make me a criminal. I have served this village for two decades."),
        (3, ["confess", "tell me the truth", "what are you hiding"],
         "I am hiding nothing! But if you want the truth, go check the old grain silo behind the mill before someone hauls the loot out of the valley.")
    ],

    "GUARD": [
        # --- GREETINGS ---
        (1, ["hi", "hello", "halt", "good day", "hey guard", "officer"],
         "Halt! Village guard on duty. State your name and business in this settlement."),
        (2, ["how are you", "how goes the patrol", "how are things"],
         "Tense. The village is on lockdown after the incident at the council vault last night."),
        (3, ["who are you", "what is your duty", "what is your job"],
         "Captain of the village watch. I patrol the gate, market, and perimeter walls."),

        # --- ALIBI & PATROL TOPIC ---
        (1, ["where were you", "what were you doing", "what were you doing last night", "where were you during the robbery"],
         "Conducting my scheduled patrols along the perimeter wall and checking the north gate as assigned."),
        (2, ["did you fall asleep", "were you sleeping", "you fell asleep", "be honest about your watch"],
         "Insolence! Though... truth be told, I had a sudden spell of dizziness around the second hour after midnight. I rested my eyes briefly at the post."),
        (3, ["why were you dizzy", "was your drink spiked", "did someone drug you"],
         "The spiced cider flask left at my watchpost tasted strangely sharp. When I woke, the post lantern was cold and the hour candle had burnt down."),

        # --- THEFT TOPIC ---
        (1, ["what happened", "what happened last night", "tell me about the robbery", "there was a robbery"],
         "The council treasury vault was breached between midnight and dawn. A sizable sum of tax gold is gone."),
        (2, ["who has the key", "how did they enter", "where is the key"],
         "The vault requires two brass keys. The council keeps one, and my locked desk drawer holds the duplicate."),
        (3, ["is the duplicate key safe", "check the desk", "did someone steal the key"],
         "I checked the desk at daybreak. The drawer lock was picked with a thin wedge and the duplicate key is missing!"),

        # --- SUSPECTS TOPIC ---
        (1, ["who did it", "who is the thief", "who do you suspect", "any idea who is it"],
         "We are interrogating everyone who lacked an alibi after curfew. The shopkeeper was up late, and the farmer has grievances."),
        (2, ["who visited the guard house", "who was near your desk", "who had access"],
         "The farmer was leaning over my desk yesterday morning shouting about boundary taxes. He had ample opportunity to eye the key drawer."),
        (3, ["tell me who you think took it", "who is the prime suspect"],
         "The farmer had the motive, but the shopkeeper knew the patrol timing. I suspect they worked in tandem to move the heavy vault chest.")
    ],

    "FARMER": [
        # --- GREETINGS ---
        (1, ["hi", "hello", "good day", "hey farmer"],
         "Good day. I am busy mending this plow before the rains come. What do you want?"),
        (2, ["how are you", "how is the harvest", "how are things"],
         "Tired and aggravated. Bad crops this season, and the village council keeps squeezing us for taxes."),
        (3, ["who are you", "what do you do"],
         "I farm the plots south of the mill. Barley, root vegetables, and draught horses."),

        # --- ALIBI TOPIC ---
        (1, ["where were you", "what were you doing last night", "where were you last night"],
         "Sleeping in my farmhouse like any honest laborer who rises before dawn."),
        (2, ["were you asleep the whole night", "did you hear anything", "can anyone vouch"],
         "I was in bed until the barn gate squeaked around midnight. I thought it was just the wind catching the latch."),
        (3, ["did you check the barn", "what happened at midnight"],
         "I threw on my coat and went out with a torch. My draught horse was hitched and my farm wagon was already rolling down the lane!"),

        # --- TOOLS & CART TOPIC ---
        (1, ["did you lose any tools", "are your tools missing", "what tools did you lose"],
         "My heavy iron crowbar and two splitting wedges vanished from my shed two days ago. I told the guard, but he did nothing."),
        (2, ["about that cart", "is your cart in the barn", "did someone take your cart"],
         "Someone took my wagon without permission. I found fresh wagon wheel ruts heading down the overgrown mill lane at dawn."),
        (3, ["who took the cart", "did you see who was driving"],
         "I saw two figures on the seat. The passenger wore a thick wool coat with polished brass buttons—identical to the shopkeeper's coat!"),

        # --- SUSPECTS & MOTIVE ---
        (1, ["who did it", "who is the thief", "who do you suspect"],
         "I hear the council vault was cleaned out. Frankly, hard to feel sorry for corrupt officials hoarding our tax coin."),
        (2, ["did you steal it", "are you the thief", "did you rob the vault"],
         "Watch your mouth! I grow crops, I do not pick vault locks. Go question the shopkeeper who sells the tools and canvas sacks."),
        (3, ["where did the wagon go", "where is the loot"],
         "The wagon ruts lead straight to the cellar under the old mill waterwheel. If you want proof, that is where the sacks are stashed.")
    ],

    "KID": [
        # --- GREETINGS ---
        (1, ["hi", "hello", "hey kid", "hey there", "hey"],
         "Hey! You look like an adventurer! Are you here to investigate the big mystery?"),
        (2, ["who are you", "what are you doing"],
         "I am Pip! I know every rooftop, ladder, and loose fence board in this whole village!"),

        # --- OBSERVATIONS & SIGHTINGS ---
        (1, ["what happened", "what happened last night", "tell me what happened"],
         "The big iron door at the vault was opened and all the council treasure chest bags vanished into thin air!"),
        (2, ["what did you see", "did you see anything last night", "did you see anyone"],
         "I stayed up watching from my loft window! I saw two shadows sneaking past the bakery with a lantern covered by a cloth!"),
        (3, ["who were the shadows", "did you see their faces", "tell me more"],
         "One shadow was huge and carrying a gigantic bulging sack! They made a bird whistle sound, 'Twit-twoo!' to signal a cart down the lane!"),

        # --- CLUES & EVIDENCE ---
        (1, ["did they drop anything", "did you find clues", "any evidence"],
         "One of them dropped a crumpled paper in the gravel! It smelled like cinnamon and dried cloves!"),
        (2, ["what was on the paper", "show me the paper", "what did the paper say"],
         "It was a receipt from the general store! It lists 'Three heavy canvas sacks and fifteen paces hemp cord' dated yesterday afternoon!"),
        (3, ["where are they hiding the loot", "where did the cart go"],
         "I followed the wheel tracks this morning! They hid the wagon under piles of dry straw behind the abandoned mill waterwheel!")
    ],

    "OLD_MAN": [
        # --- GREETINGS ---
        (1, ["hi", "hello", "greetings", "good day"],
         "Peace be upon your travels, traveler. What brings your restless steps to an old man's porch?"),
        (2, ["who are you", "what is your story"],
         "I am Corvus. I have watched this village grow from four wooden huts to stone walls over seventy winters."),

        # --- THEFT & WISDOM ---
        (1, ["what happened", "what happened last night"],
         "Greed has visited our quiet settlement. The vault was emptied under the veil of the new moon."),
        (2, ["who is the thief", "who do you think did it", "who had a motive"],
         "A wise person does not throw stones into the dark. Look for who had the motive, the means, and the keys."),
        (3, ["tell me what you know", "reveal the truth", "who really did it"],
         "The vault lock was forged in the capital forty years ago. It cannot be forced without noise; it was opened with the duplicate key taken while the guard slept."),

        # --- SIGHTINGS & SECRETS ---
        (1, ["did you see anything", "did you hear anything", "what did you see"],
         "Around the third bell after midnight, the guard's customary patrol whistle failed to sound. Silence fell over the square."),
        (2, ["did you see lights", "did you see someone outside"],
         "A shutter opened at the back of the general store, and a dim amber flame moved swiftly along the shadows toward the mill trail."),
        (3, ["where is the key", "where is the evidence hidden"],
         "The stolen duplicate key is buried beneath the third flagstone behind the shopkeeper's rainwater barrel. Uncover it, and the truth will be plain to all.")
    ]
}

new_samples = []

tier_to_trust = {
    1: ["LOW", "MEDIUM"],
    2: ["LOW", "MEDIUM", "HIGH"],
    3: ["MEDIUM", "HIGH"]
}

for npc, entries in MULTI_TIER_DIALOGUES.items():
    for tier, queries, response in entries:
        assigned_trusts = tier_to_trust.get(tier, ["LOW"])
        for q in queries:
            for trust in assigned_trusts:
                for mood in ["friendly", "calm", "suspicious", "defensive"]:
                    line = f"<|npc|>{npc}<|trust|>{trust}<|memory|>tier{tier}<|mood|>{mood}<|input|>{q}<|response|>{response}<|end|>"
                    new_samples.append(line)

print(f"Generated {len(new_samples)} multi-tier dialogue turns.")

# Combine base dataset + multi-tier dialogue turns
all_master_lines = base_lines + new_samples
print(f"Total master training set: {len(all_master_lines)} samples.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(all_master_lines) + "\n")

print(f"Saved master multi-tier dataset to {OUTPUT_FILE}")
