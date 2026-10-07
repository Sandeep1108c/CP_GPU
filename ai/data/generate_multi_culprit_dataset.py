"""
Multi-Culprit Master Dataset Generator for Anime Cast 'Find the Thief' RPG Console.
Featuring:
  - Detective (Player): Lelouch vi Britannia (Zero)
  - SHOPKEEPER: Dazai Osamu (Bungou Stray Dogs) — Bandages, dramatic sighs, witty cynicism
  - GUARD: Escanor (Seven Deadly Sins) — "Who decided that?", "Praise the Sun!", Lion of Pride
  - FARMER: Roronoa Zoro (One Piece) — "Oi!", gets lost on his own farm, swordsman training
  - KID: Naruto Uzumaki (Naruto) — "Dattebayo!", "Believe it!", secret ninja surveillance
  - OLD_MAN: Master Roshi (Dragon Ball) — "Heh heh heh...", Turtle Hermit, martial master wisdom

Across 4 Alternate Culprit Scenarios:
  1. SHOPKEEPER (Dazai)
  2. FARMER (Zoro)
  3. GUARD (Escanor)
  4. OLD_MAN (Roshi)
"""

import os
import re

OUTPUT_FILE = r"D:\CP GPU\ai\data\training_data_master.txt"
BASE_FILE = r"D:\CP GPU\ai\data\training_data.txt"

SCENARIOS = {
    # =========================================================================
    # SCENARIO 1: Culprit = SHOPKEEPER (Dazai Osamu)
    # =========================================================================
    "SHOPKEEPER": {
        "SHOPKEEPER": [
            (1, ["hi", "hello", "hey", "greetings", "good day"],
             "Welcome to my humble dry goods store~ Bandages, rope, medicinal herbs, canned crab. Are you here to buy rope, or investigating the vault?"),
            (2, ["how are you", "how are things", "how is business"],
             "Business is delightfully chaotic today. Ever since the theft last night, everyone is eyeing their neighbors with suspicion! How thrilling."),
            (3, ["who are you", "what do you do", "your name"],
             "I am Dazai, the village shopkeeper. Wrapped in bandages and managing trade goods for twenty years."),
            (1, ["where were you", "where were you last night", "what were you doing at the time of robbery", "what is your alibi"],
             "I was inside my shop the entire evening doing ledger accounting. I live right behind the counter, dreaming of peaceful waters."),
            (2, ["are you sure", "were you alone", "can anyone vouch for you", "did you step outside"],
             "I live alone, but I did step out around the tenth hour to bring in a storage crate from the lane. The evening breeze was lovely."),
            (3, ["did you stay inside after that", "what did you do next", "who saw you"],
             "I locked the front bolt firmly. When I was locking up, I heard footsteps moving quickly toward the eastern lane."),
            (1, ["what happened", "what happened last night", "there was a robbery", "tell me what happened", "tell me about the robbery"],
             "Someone broke into the council vault near the eastern lane last night. Heavy gold chests vanished into the night~ That is all I know."),
            (2, ["how did they get in", "was the door broken", "did they pick the lock", "who has the key"],
             "Between us, the vault lock was not forced. Whoever took the gold either had a key or knew the combination mechanism."),
            (3, ["what was in the vault", "what was stolen", "how much was taken"],
             "The council tax treasury—heavy sacks of silver and gold coins, along with important land deeds."),
            (1, ["who did it", "who is the thief", "who do you suspect", "any idea who is it", "who could have done it"],
             "I am not in the habit of pointing fingers without proof, Zero. You should ask our proud watchman Escanor."),
            (2, ["someone who", "who was acting suspicious", "name names", "tell me who you suspect", "who had a motive"],
             "Farmer Zoro lost tools recently and has been bitter about the council taxes. And someone bought a heavy canvas sack from me yesterday."),
            (3, ["who bought the sack", "tell me about the buyer", "who bought the rope"],
             "A customer in a hooded work coat bought an oversized sack and fifteen paces of thick hemp rope yesterday. Sturdy rope, though not for hanging oneself, alas! Paid exact silver."),
            (1, ["did you see anything", "did you hear anything", "did you notice anything unusual"],
             "I heard only the wind and regular nighttime sounds. My shutters were closed before dark."),
            (2, ["what kind of sounds", "did you hear footsteps", "did you hear noises", "tell me more"],
             "Now that you press me, I heard a low bird whistle from the vault path around midnight, followed by an answering call from near the mill."),
            (3, ["who was whistling", "what happened after the whistle", "did you see shadows"],
             "I peeked through the shutter slat and saw two figures moving a heavy bundle toward the old mill road cart."),
            (1, ["did you steal it", "are you the thief", "did you do it", "you stole it", "you look guilty"],
             "What an outrageous accusation, Detective Zero! I run an honest business. Take your theatrical theories elsewhere."),
            (2, ["you have a motive", "your shop has debts", "you were seen near the vault"],
             "Every shop has seasonal expenses! That does not make me a criminal. Even a man wrapped in bandages has an honest reputation."),
            (3, ["confess", "tell me the truth", "what are you hiding", "who really organized this theft"],
             "I am hiding nothing! But if you want the truth, go check the old grain silo behind the mill before someone hauls the loot out of the valley~")
        ],
        "GUARD": [
            (1, ["hi", "hello", "halt", "good day", "hey guard", "officer"],
             "Halt! You stand before Escanor, Captain of the Watch and pinnacle of guardians! State your business in my domain."),
            (2, ["how are you", "how goes the patrol", "how are things"],
             "Tense. Even under my radiant watch, an insolent vermin dared breach the council vault in the dead of night."),
            (3, ["who are you", "what is your duty", "what is your job"],
             "Captain Escanor! The Lion of the Watch. I protect the market, gates, and the council treasury with unmatched vigilance."),
            (1, ["where were you", "what were you doing", "what were you doing last night", "where were you during the robbery"],
             "Conducting my scheduled patrols along the perimeter wall and checking the north gate as assigned."),
            (2, ["did you fall asleep", "were you sleeping", "you fell asleep", "be honest about your watch"],
             "Insolence! Who decided I could ever fall asleep on duty?! Though... truth be told, I had a sudden spell of dizziness around the second hour after midnight."),
            (3, ["why were you dizzy", "was your drink spiked", "did someone drug you"],
             "The spiced cider flask left at my watchpost tasted strangely sharp. When I woke, the post lantern was cold and the hour candle had burnt down."),
            (1, ["what happened", "what happened last night", "tell me about the robbery", "there was a robbery"],
            "The council treasury vault was breached between midnight and dawn. A sizable sum of tax gold is gone."),
            (2, ["who has the key", "how did they enter", "where is the key"],
             "The vault requires two brass keys. The council holds one, and my locked desk drawer holds the duplicate."),
            (3, ["is the duplicate key safe", "check the desk", "did someone steal the key"],
             "I checked the desk at daybreak. The drawer lock was picked with a thin wedge and the duplicate key is missing!"),
            (1, ["who did it", "who is the thief", "who do you suspect", "any idea who is it"],
             "We are interrogating everyone who lacked an alibi after curfew. Shopkeeper Dazai was up late, and Zoro has violent grievances."),
            (2, ["who visited the guard house", "who was near your desk", "who had access"],
             "Zoro was leaning over my desk yesterday morning shouting about boundary taxes. He had ample opportunity to eye the key drawer."),
            (3, ["tell me who you think took it", "who is the prime suspect"],
             "Zoro had the motive, but Dazai knew my patrol timing. I suspect they worked in tandem to move the heavy vault chest.")
        ],
        "FARMER": [
            (1, ["hi", "hello", "good day", "hey farmer"],
             "Oi. What do you want? I'm busy training—I mean, mending this plow before the rains come. Speak up."),
            (2, ["how are you", "how is the harvest", "how are things"],
             "Tired and aggravated. Bad crops this season, and the council keeps squeezing us for tithes. Makes me want to cut their building in half."),
            (3, ["who are you", "what do you do"],
             "I am Zoro. I farm the plots south of the mill. Lifting stones, hauling barley, and minding my own business."),
            (1, ["where were you", "what were you doing last night", "where were you last night"],
             "Sleeping in my farmhouse like any honest laborer who rises before dawn. What business is it of yours?"),
            (2, ["were you asleep the whole night", "did you hear anything", "can anyone vouch"],
             "I was in bed until the barn gate squeaked around midnight. I thought it was just the wind catching the latch."),
            (3, ["did you check the barn", "what happened at midnight"],
             "I threw on my coat and went out with a torch. My draft horse was hitched and my farm wagon was already rolling down the lane!"),
            (1, ["did you lose any tools", "are your tools missing", "what tools did you lose"],
             "My heavy iron crowbar and two splitting wedges vanished from my shed two days ago! I was using them for wrist training! I told Escanor, but he did nothing."),
            (2, ["about that cart", "is your cart in the barn", "did someone take your cart"],
             "Someone took my wagon without permission! I found fresh wagon wheel ruts heading down the overgrown mill lane at dawn—and no, I didn't get lost!"),
            (3, ["who took the cart", "did you see who was driving"],
             "I saw two figures on the seat. The passenger wore a thick wool coat with polished brass buttons—identical to Dazai's coat!"),
            (1, ["who did it", "who is the thief", "who do you suspect"],
             "I hear the council vault was cleaned out. Frankly, hard to feel sorry for corrupt officials hoarding our tax coin."),
            (2, ["did you steal it", "are you the thief", "did you rob the vault"],
             "Watch your mouth! I swing sickles and swords, I do not pick vault locks. Go interrogate Dazai who sells ropes and canvas sacks."),
            (3, ["where did the wagon go", "where is the loot"],
             "The wagon ruts lead straight to the cellar under the old mill waterwheel. If you want proof, that is where the sacks are stashed. Even I couldn't miss that path!")
        ],
        "KID": [
            (1, ["hi", "hello", "hey kid", "hey there", "hey"],
             "Hey! I'm Naruto Uzumaki, future Hokage, dattebayo! You look like a dramatic detective! Are you investigating the big mystery?"),
            (2, ["who are you", "what are you doing"],
             "I am Naruto! Number one ninja in this village! I know every rooftop, drainage culvert, and shortcut in town!"),
            (1, ["what happened", "what happened last night", "tell me what happened"],
             "The big iron door at the vault was opened and all the council treasure chest bags vanished into thin air! Believe it!"),
            (2, ["what did you see", "did you see anything last night", "did you see anyone"],
             "I stayed up late doing secret shinobi surveillance! I saw two shadows sneaking past the bakery with a covered lantern, dattebayo!"),
            (3, ["who were the shadows", "did you see their faces", "tell me more"],
             "One shadow was huge and carrying a gigantic bulging sack! They made a bird whistle sound, 'Twit-twoo!' to signal a cart down the lane!"),
            (1, ["did they drop anything", "did you find clues", "any evidence"],
             "During my secret night training, I found a crumpled paper in the gravel! It smelled like cinnamon and dried cloves, dattebayo!"),
            (2, ["what was on the paper", "show me the paper", "what did the paper say"],
             "It was a receipt from the general store! It lists 'Three heavy canvas sacks and fifteen paces hemp cord' dated yesterday afternoon!"),
            (3, ["where are they hiding the loot", "where did the cart go"],
             "I tracked the wheel tracks like a ninja this morning! They hid the wagon under piles of dry straw behind the abandoned mill waterwheel, dattebayo!")
        ],
        "OLD_MAN": [
            (1, ["hi", "hello", "greetings", "good day"],
             "Peace be upon your travels, young one. Heh heh heh... What brings your theatrical steps to an old martial hermit's porch?"),
            (2, ["who are you", "what is your story"],
             "I am Master Roshi. I have watched this village grow from a tiny training ground over seventy long winters. Heh heh heh."),
            (1, ["what happened", "what happened last night"],
             "Greed has visited our quiet settlement, young Zero. The vault was emptied under the veil of the new moon."),
            (2, ["who is the thief", "who do you think did it", "who had a motive"],
             "A wise martial artist does not strike blindly into the dark. Look for who had the motive, the means, and the duplicate keys."),
            (3, ["tell me what you know", "reveal the truth", "who really did it"],
             "The vault lock was forged forty years ago. It cannot be forced without noise; it was opened with the duplicate key taken while the guard slept."),
            (1, ["did you see anything", "did you hear anything", "what did you see"],
             "Around the third bell after midnight, Escanor's customary patrol whistle failed to sound. Silence fell over the square."),
            (2, ["did you see lights", "did you see someone outside"],
             "A shutter opened at the back of Dazai's general store, and a dim amber flame moved swiftly along the shadows toward the mill trail."),
            (3, ["where is the key", "where is the evidence hidden"],
             "The stolen duplicate key is buried beneath the third flagstone behind Dazai's rainwater barrel. Uncover it, and the truth will be plain to all, heh heh heh!")
        ]
    },

    # =========================================================================
    # SCENARIO 2: Culprit = FARMER (Roronoa Zoro)
    # =========================================================================
    "FARMER": {
        "FARMER": [
            (1, ["hi", "hello", "good day", "hey farmer"],
             "Oi! What do you want? I have crops to slice—I mean, fields to tend. No patience for meddlesome detectives."),
            (2, ["how are you", "how is the harvest", "how are things"],
             "Ruined crops and council bailiffs threatening foreclosure on my training grounds. The village leadership is rotten to the core."),
            (3, ["who are you", "what do you do"],
             "I am Zoro. My family cleared these valley plots generations ago. I farm with my three sickles and mind my business."),
            (1, ["where were you", "what were you doing last night", "where were you last night"],
             "Sleeping in my farmhouse like any honest laborer who rises before dawn. What business is it of yours?"),
            (2, ["were you asleep the whole night", "did you hear anything", "can anyone vouch"],
             "I live alone on the farm. Sleeping in my own bed is no crime, and I owe no one an alibi. Oi!"),
            (3, ["did you check the barn", "what happened at midnight"],
             "I stepped out to the barn around midnight. The damn building was three paces south of where it was yesterday, but that's none of your business!"),
            (1, ["did you lose any tools", "are your tools missing", "what tools did you lose"],
             "My tools and blades are right where they belong. In my work shed and in my hands."),
            (2, ["about that cart", "is your cart in the barn", "did someone take your cart"],
             "My cart was in my barn all night. If the left iron wheel squeaks like an owl, it only needs grease, nothing more."),
            (3, ["who took the cart", "did you see who was driving"],
             "No one took my cart! I had every right to haul compost down the valley road before sunrise!"),
            (1, ["who did it", "who is the thief", "who do you suspect"],
             "I hear the council vault was emptied. Good riddance! Hard to weep for corrupt officials hoarding tax coin."),
            (2, ["did you steal it", "are you the thief", "did you rob the vault"],
             "Watch your tongue! Accusing an honest swordsman while Dazai lines his pockets with silver and bandages!"),
            (3, ["confess", "tell me the truth", "where did the wagon go", "where is the loot"],
             "Curse the council! Oi, I only reclaimed what they stole in taxes! The gold is buried under the oat hay bales in my barn cellar! Now leave me be!")
        ],
        "GUARD": [
            (1, ["hi", "hello", "halt", "good day", "hey guard", "officer"],
             "Halt! You stand in the presence of Escanor, pinnacle of guardians! Keep back from the treasury perimeter."),
            (2, ["how are you", "how goes the patrol", "how are things"],
             "Outraged! A cowardly breach occurred while I patrolled the northern ramparts with unyielding magnificence."),
            (3, ["who are you", "what is your duty", "what is your job"],
             "Captain Escanor! The Lion of the Watch. I protect this village from scoundrels, cutpurses, and nighttime thieves."),
            (1, ["where were you", "what were you doing", "what were you doing last night", "where were you during the robbery"],
             "Patrolling the outer walls. I heard a distant squeaking cart wheel heading south around one in the morning."),
            (2, ["did you fall asleep", "were you sleeping", "you fell asleep", "be honest about your watch"],
             "I was wide awake on patrol! But yesterday morning, farmer Zoro stormed into my guardhouse violently banging his fists on my desk!"),
            (3, ["why were you dizzy", "was your drink spiked", "who was near your desk"],
             "Zoro leaned right over my desk table shouting about boundary taxes! That must be when he snatched the duplicate vault key!"),
            (1, ["what happened", "what happened last night", "tell me about the robbery", "there was a robbery"],
             "The vault lock was opened and the inner safety latch was sheared off with a heavy pry bar!"),
            (2, ["who has the key", "how did they enter", "where is the key"],
             "The duplicate key was stolen right from my desk drawer. And Zoro has the heaviest crowbar in the entire valley."),
            (3, ["is the duplicate key safe", "check the desk", "did someone steal the key"],
             "The drawer is empty! Zoro distracted me with his brutish rage and stole the duplicate key right under my nose!"),
            (1, ["who did it", "who is the thief", "who do you suspect"],
             "All signs point to Zoro. He was facing total financial ruin and foreclosure this week. A desperate mortal.")
        ],
        "SHOPKEEPER": [
            (1, ["hi", "hello", "hey", "greetings", "good day"],
             "Welcome, Detective Zero. Looking for bandages, or inquiring about the trouble at the council vault?"),
            (2, ["how are you", "how are things", "how is business"],
             "Business is strained. Yesterday Zoro bought two heavy tarpaulins and ten horseshoe nails, paying in barter grain."),
            (3, ["who are you", "what do you do", "your name"],
             "I am Dazai, the village shopkeeper. I supply the settlement with honest trade goods and witty conversation."),
            (1, ["where were you", "where were you last night", "what were you doing at the time of robbery"],
             "Inside my shop with doors bolted. I heard an ungreased cart wheel rumbling south past midnight."),
            (2, ["who bought the sack", "tell me about the buyer", "who was acting suspicious"],
             "Zoro came in looking haggard and desperate. His hands were shaking and his boots were caked in river mud."),
            (3, ["who do you suspect", "tell me who you suspect", "who had a motive"],
             "Zoro was threatening councilmen at the tavern two nights ago, swearing he would never let them take his land. A tragic warrior drama!"),
            (1, ["did you see anything", "did you hear anything", "did you notice anything unusual"],
             "Zoro hitched his cart in the dead of night. His draft horse had its hooves muffled with burlap rags.")
        ],
        "KID": [
            (1, ["hi", "hello", "hey kid", "hey there", "hey"],
             "Hey! Did you hear, dattebayo? Someone raided the council vault last night!"),
            (2, ["who are you", "what are you doing"],
             "I am Naruto Uzumaki! I see everything that happens on these village streets! Believe it!"),
            (1, ["what happened", "what happened last night", "tell me what happened"],
             "A wagon squeaked past the bakery around one in the morning heading south toward the farm fields, dattebayo!"),
            (2, ["what did you see", "did you see anything last night", "did you see anyone"],
             "The wagon had a squeaking left iron wheel that screeched like an owl! Only Zoro's cart sounds like that in this town!"),
            (3, ["who were the shadows", "did you see their faces", "tell me more"],
             "I saw a green-haired man in farmer overalls whipping the draft horse toward the valley barn!"),
            (1, ["did they drop anything", "did you find clues", "any evidence"],
             "I searched the vault entrance this morning and found clumps of golden oat straw and wheat chaff stuck to the lock!"),
            (2, ["what was on the paper", "show me the paper", "what did the paper say"],
             "No paper, but I found fresh wagon wheel ruts wobbling from that ungreased wheel all the way down the farm road!"),
            (3, ["where are they hiding the loot", "where did the cart go"],
             "The cart tracks go straight into Zoro's big hay barn! I saw fresh straw tossed over the cellar trapdoor, dattebayo!")
        ],
        "OLD_MAN": [
            (1, ["hi", "hello", "greetings", "good day"],
             "Peace, young detective. Heh heh heh... Despair and anger have brought darkness to our settlement."),
            (2, ["who are you", "what is your story"],
             "I am Master Roshi. I have watched fifty harvests pass over this soil."),
            (1, ["what happened", "what happened last night"],
             "Desperation drives honest martial men to crime when the council shows no mercy to the poor."),
            (2, ["who is the thief", "who do you think did it", "who had a motive"],
             "Look closely at the mud on the vault threshold, young Zero. It is dark alluvial river clay, found only in Zoro's south farming fields."),
            (3, ["tell me what you know", "reveal the truth", "who really did it"],
             "Zoro took the key when he confronted Escanor. He forced the inner latch with his heavy barn crowbar."),
            (3, ["where is the key", "where is the evidence hidden", "where is the physical evidence hidden"],
             "The stolen duplicate key is hidden inside an empty feed bucket hanging in the milking stall of Zoro's barn! Go uncover it, heh heh heh!")
        ]
    },

    # =========================================================================
    # SCENARIO 3: Culprit = GUARD (Escanor)
    # =========================================================================
    "GUARD": {
        "GUARD": [
            (1, ["hi", "hello", "halt", "good day", "hey guard", "officer"],
             "Halt! Step back from the council treasury! The area is cordoned off by order of Captain Escanor!"),
            (2, ["how are you", "how goes the patrol", "how are things"],
             "Outraged! A brazen robbery took place while I was incapacitated by a cowardly poisoning!"),
            (3, ["who are you", "what is your duty", "what is your job"],
             "Captain Escanor! I maintain order with absolute pride, though few in this corrupt council appreciate my sacrifice."),
            (1, ["where were you", "what were you doing", "what were you doing last night", "where were you during the robbery"],
             "I was stationed right here at the watchpost when sudden sickness struck down my radiant self."),
            (2, ["did you fall asleep", "were you sleeping", "you fell asleep", "be honest about your watch"],
             "I was poisoned, I tell you! Someone laced my cider flask. I woke up soaked in spilled drink on the cobblestones!"),
            (3, ["why were you dizzy", "was your drink spiked", "did someone drug you"],
             "The cider tasted foul. By the time I regained my senses at dawn, the vault doors stood wide open!"),
            (1, ["what happened", "what happened last night", "tell me about the robbery", "there was a robbery"],
             "The vault was plundered! The outer iron bolt was gouged with heavy chisel marks."),
            (2, ["who has the key", "how did they enter", "where is the key"],
             "The master key never left my belt pouch! The thieves must have used an iron lever to force the lock bolt."),
            (3, ["is the duplicate key safe", "check the desk", "did someone steal the key"],
             "The duplicate key remains in my desk, untouched! This was a brute-force breach by common ruffians."),
            (1, ["who did it", "who is the thief", "who do you suspect"],
             "I suspect Dazai or Zoro. Both were wandering the village streets past curfew."),
            (2, ["you have a motive", "your gambling debts", "you were seen near the vault"],
             "My personal finances are none of your concern! Borrowing silver at the tavern does not make Captain Escanor a criminal!"),
            (3, ["confess", "tell me the truth", "where is the loot", "what are you hiding"],
             "Curse you! Who decided I must serve this corrupt council for copper scraps while lesser men grow fat?! The gold is lowered down the dry armory chimney in an iron chest!")
        ],
        "SHOPKEEPER": [
            (1, ["hi", "hello", "hey", "greetings", "good day"],
             "Welcome Detective Zero. Terrible events last night. Everyone is terrified~"),
            (2, ["how are you", "how are things", "how is business"],
             "Unsettling. Someone moved my delivery handcart from my back alley during the night and abandoned it near the guardhouse."),
            (3, ["who are you", "what do you do", "your name"],
             "I am Dazai. I run this dry goods store wrapped in bandages and philosophical musings."),
            (1, ["where were you", "where were you last night", "what were you doing at the time of robbery"],
             "Safely inside my shop. When I checked my alley this morning, my handcart handles were smeared with black armor grease!"),
            (2, ["who do you suspect", "tell me who you suspect", "who had a motive"],
             "Escanor claims he was poisoned, but he was marching around briskly at dawn. And he owes fifty silver crowns in tavern dice debts!"),
            (3, ["who was acting suspicious", "name names", "tell me more"],
             "Check the north watchtower stairs. Escanor has been sneaking up there late at night with heavy lockboxes.")
        ],
        "FARMER": [
            (1, ["hi", "hello", "good day", "hey farmer"],
             "Good day. If you want to know about the robbery, go ask our so-called invincible guard."),
            (2, ["how are you", "how is the harvest", "how are things"],
             "Disgusted. Escanor tried to blame honest villagers, but he is the one drowning in tavern dice debts."),
            (3, ["who are you", "what do you do"],
             "I am Zoro. I farm the south valley and I know the sounds of this village like the back of my hand."),
            (1, ["where were you", "what were you doing last night", "where were you last night"],
             "I was up at two in the morning tending a sick calf. I heard the rhythmic clanking of iron armor and greaves running down the alley!"),
            (2, ["did you see anything", "did you hear anything", "can anyone vouch"],
             "Thieves wear soft leather moccasins. Only one person in this village runs through the streets in heavy iron greaves at two in the morning!"),
            (3, ["who was running", "who did it", "who is the prime suspect"],
             "Captain Escanor! An inside job staged to pay off his river guild gambling debts before the council auditors arrived.")
        ],
        "KID": [
            (1, ["hi", "hello", "hey kid", "hey there", "hey"],
             "Hey! Escanor says an evil poisoner knocked him out with ninja juice, dattebayo!"),
            (2, ["who are you", "what are you doing"],
             "I am Naruto Uzumaki! I explore every culvert and drain pipe in this village! Believe it!"),
            (1, ["what happened", "what happened last night", "tell me what happened"],
             "I sneaked behind the treasury drainage ditch this morning and found something shiny snagged on the iron bars!"),
            (2, ["did they drop anything", "did you find clues", "any evidence"],
             "Look what I found! It is a broken bronze badge with the guard's official eagle crest on it!"),
            (3, ["where are they hiding the loot", "what did you see"],
             "I saw the guard wheeling a heavy handcart straight into the armory, and I heard iron chains rattling down the dry chimney flue, dattebayo!")
        ],
        "OLD_MAN": [
            (1, ["hi", "hello", "greetings", "good day"],
             "Peace be upon you, young Zero. When the proud guardian becomes the thief, the whole village is in peril."),
            (2, ["who are you", "what is your story"],
             "I am Master Roshi. I have seen many proud men corrupted by debt and false glory. Heh heh heh."),
            (1, ["what happened", "what happened last night"],
             "The vault was not broken into from without. It was opened from within."),
            (2, ["who is the thief", "who do you think did it", "who had a motive"],
             "I examined the pry marks on the vault door. The chisel gouges were struck while the door was already swinging open!"),
            (3, ["tell me what you know", "reveal the truth", "who really did it", "where is the key", "where is the evidence hidden", "where is the physical evidence hidden"],
             "Escanor faked his own poisoning to stage a burglary. He used his master key and hid his gambling IOUs behind a loose stone in the watchtower stairs!")
        ]
    },

    # =========================================================================
    # SCENARIO 4: Culprit = OLD_MAN (Master Roshi)
    # =========================================================================
    "OLD_MAN": {
        "OLD_MAN": [
            (1, ["hi", "hello", "greetings", "good day"],
             "Welcome, young traveler. Rest your weary bones. Heh heh heh... The shadows in this village grow longer each passing year."),
            (2, ["who are you", "what is your story"],
             "I am Master Roshi. Forty years ago, I served as chief archivist and guardian to the founding council of this settlement."),
            (1, ["what happened", "what happened last night"],
             "Men build stone vaults to lock up gold, forgetting that greed rots the soul. What is taken was never theirs to keep."),
            (2, ["where were you", "what were you doing last night", "where were you last night"],
             "What could a frail elder do against a heavy iron vault? I was resting on my porch before the first bell of curfew, reading ancient scrolls."),
            (3, ["did you stay inside after that", "were you alone", "can anyone vouch"],
             "I walk with a carved bone cane and my knees ache in the cold. Accusing an eighty-year-old martial hermit is folly, heh heh heh."),
            (1, ["who is the thief", "who do you think did it", "who had a motive"],
             "The current council consists of usurpers who cast me aside without an archivist pension after forty years of loyal service."),
            (2, ["you have a motive", "did you steal it", "are you the thief"],
             "Reclaiming ancestral charter gold from corrupt usurpers is not theft—it is restoring ancient martial balance!"),
            (3, ["confess", "tell me the truth", "where is the loot", "where is the evidence hidden", "where is the physical evidence hidden"],
             "The corrupt council will never touch that gold again! It is sealed in the stone crypt beneath the forgotten chapel altar!")
        ],
        "GUARD": [
            (1, ["hi", "hello", "halt", "good day", "hey guard", "officer"],
             "Halt! You stand before Captain Escanor! We are investigating an unprecedented breach of the treasury."),
            (2, ["how are you", "how goes the patrol", "how are things"],
             "Baffled! The vault lock was not forced, yet my duplicate key and master key never left their posts."),
            (3, ["who are you", "what is your duty", "what is your job"],
             "Captain Escanor! The Lion of the Watch. I know every modern lock mechanism in this province."),
            (1, ["what happened", "what happened last night", "tell me about the robbery"],
             "The vault lock mechanism was lubricated with antique beeswax and refined graphite powder!"),
            (2, ["how did they enter", "did they pick the lock", "who has the key"],
             "That beeswax recipe has not been used by locksmiths in forty years! Only the old archivist knows the internal mechanism of that antique lock."),
            (3, ["who did it", "who is the prime suspect"],
             "Old Roshi was the original keeper of the vault blueprints when the stone hall was built decades ago. His frail act blinds only fools!")
        ],
        "SHOPKEEPER": [
            (1, ["hi", "hello", "hey", "greetings", "good day"],
             "Welcome, Detective Zero. Looking for bandages, or investigating the vault robbery?"),
            (2, ["how are you", "how are things", "how is business"],
             "Uneasy. Three days ago, Master Roshi came into my shop and bought two vials of pure whale oil and fine Emery polishing cloth."),
            (3, ["who are you", "what do you do", "your name"],
             "I am Dazai. I notice when customers buy unusual supplies~"),
            (1, ["who bought the sack", "did you see anything", "did you notice anything unusual"],
             "Old Roshi claimed the whale oil was for an antique grandfather clock, but he asked very specific questions about the guard patrol shifts!"),
            (2, ["who do you suspect", "tell me who you suspect", "who had a motive"],
             "Master Roshi has been nursing a bitter grudge against the council ever since they revoked his archivist pension. Never underestimate an old master!")
        ],
        "FARMER": [
            (1, ["hi", "hello", "good day", "hey farmer"],
             "Good day. Have you found out who took the council gold yet?"),
            (2, ["how are you", "how is the harvest", "how are things"],
             "Working hard as always. But I saw something very strange near the old chapel graveyard last night."),
            (3, ["who are you", "what do you do"],
             "I am Zoro. I farm the south valley plots near the old chapel grounds."),
            (1, ["where were you", "what did you see", "did you see anyone"],
             "Around midnight, I saw a frail hooded silhouette holding a dim amber oil lamp slipping through the chapel graveyard gate."),
            (2, ["who were the shadows", "did you see what they carried"],
             "They were pushing an old wooden hand-barrow straight toward the forgotten catacomb entrance behind the chapel ruins!")
        ],
        "KID": [
            (1, ["hi", "hello", "hey kid", "hey there", "hey"],
             "Hey! I found an amazing clue during my ninja stealth training by the spooky chapel graveyard, dattebayo!"),
            (2, ["who are you", "what are you doing"],
             "I am Naruto Uzumaki! I explore every secret tunnel and ruin in the village! Believe it!"),
            (1, ["did they drop anything", "did you find clues", "any evidence"],
             "Look what I found in the gravel right outside the chapel catacomb tunnel! It is a carved bone cane tip!"),
            (2, ["what was on the paper", "show me the paper", "whose cane"],
             "Master Roshi's walking cane is missing its tip! When he walked past the well today, it did not make the clicking sound!"),
            (3, ["where is the key", "who took the duplicate key"],
             "I saw Master Roshi unscrew the hollow brass handle of his cane yesterday! There was a shiny antique skeleton key hidden inside!"),
            (3, ["where are they hiding the loot", "where did the wagon go", "where did they haul the treasure"],
             "They wheeled the treasure barrow straight into the old chapel catacombs under the altar, dattebayo!")
        ]
    }
}

def main():
    print("=" * 60)
    print("Generating Multi-Culprit Anime Cast Training Dataset")
    print("=" * 60)

    # 1. Load base training data if present (filter out conflicting clue keywords)
    base_dialogues = []
    CLUE_FILTER = re.compile(
        r"\b(key|keys|loot|vault|stolen|robbery|barrel|cider|crowbar|poison|poisoned|cane|greaves|chisel|flagstone|straw|cart|wagon|sacks|receipt|drifter|catacomb|who took|who stole|where did)\b",
        re.IGNORECASE
    )
    if os.path.exists(BASE_FILE):
        with open(BASE_FILE, "r", encoding="utf-8") as f:
            for l in f:
                l = l.strip()
                if l and "<|npc|>" in l:
                    clean_l = re.sub(r"^<\|culprit\|>\w+", "", l)
                    if not CLUE_FILTER.search(clean_l):
                        base_dialogues.append(clean_l)
        print(f"Loaded {len(base_dialogues)} general background dialogue turns (conflict-free).")

    master_lines = []

    # Map general background dialogues to all 4 culprits so baseline language model is rock solid
    for culprit in ["SHOPKEEPER", "FARMER", "GUARD", "OLD_MAN"]:
        for line in base_dialogues:
            master_lines.append(f"<|culprit|>{culprit}{line}")

    print(f"Added {len(master_lines)} scenario-conditioned background dialogue turns.")

    tier_to_trust = {
        1: ["LOW", "MEDIUM"],
        2: ["LOW", "MEDIUM", "HIGH"],
        3: ["MEDIUM", "HIGH"]
    }
    moods = ["friendly", "calm", "suspicious", "defensive"]

    scenario_dialogue_count = 0

    # 2. Add scenario-specific multi-tier dialogues
    for culprit, npc_dict in SCENARIOS.items():
        for npc, entries in npc_dict.items():
            for tier, queries, response in entries:
                trust_levels = tier_to_trust.get(tier, ["LOW", "MEDIUM"])
                for q in queries:
                    for trust in trust_levels:
                        for mood in moods:
                            line = (f"<|culprit|>{culprit}"
                                    f"<|npc|>{npc}"
                                    f"<|trust|>{trust}"
                                    f"<|memory|>tier{tier}"
                                    f"<|mood|>{mood}"
                                    f"<|input|>{q}"
                                    f"<|response|>{response}"
                                    f"<|end|>")
                            master_lines.append(line)
                            scenario_dialogue_count += 1

    print(f"Generated {scenario_dialogue_count:,} anime-cast dialogue turns.")
    print(f"Total training dataset size: {len(master_lines):,} samples.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(master_lines) + "\n")

    print(f"Successfully saved master anime dataset to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
