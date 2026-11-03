/**
 * @file esp32_gpu_demo.ino
 * @brief "Catch the Thief" — Full 60 FPS Interactive Anime Detective RPG & AI Engine
 * @project Custom FPGA-Based GPU & Edge AI Console — Woxsen University
 * @target ESP32 / ESP32-S3 -> Gowin GW2AR-18C Tang Nano 20K (GPU)
 *
 * Wiring (ESP -> Tang Nano 20K Header):
 *   GND      -> GND    (Common Ground - essential!)
 *   PIN_CS   -> Pin 86 (SPI CS_N)
 *   PIN_SCLK -> Pin 49 (SPI SCLK)
 *   PIN_MOSI -> Pin 48 (SPI MOSI)
 *   PIN_MISO -> Pin 51 (SPI MISO)
 *
 * Interactive Serial Commands (115200 baud):
 *   - Type any natural question (e.g., "where were you last night", "what was stolen",
 *     "was your drink spiked", "who bought the sacks", "whose cane", "confess", "where is the loot")
 *   - /shopkeeper (/dazai or 1) : Walk Zero to Dazai's General Store (NW)
 *   - /guard      (/escanor or 2): Walk Zero to Escanor at Council Treasury (NE)
 *   - /farmer     (/zoro or 3)   : Walk Zero to Zoro's Barn & Old Mill (SE)
 *   - /kid        (/naruto or 4) : Walk Zero to Naruto at Central Town Well (Center)
 *   - /old_man    (/roshi or 5)  : Walk Zero to Master Roshi's Porch & Chapel (SW)
 *   - /culprit <name>            : Set active culprit scenario (shopkeeper, farmer, guard, old_man)
 *   - /accuse <name>             : Formally accuse a suspect of the robbery!
 *   - /tour                      : Resume autonomous village patrol & demo interrogation
 *   - /help                      : Print available commands & investigation status
 */

#include "gpu_commands.h"
#include "sprites.h"
#include "ai_dialogue_table.h"

// =============================================================================
// Pin Configurations
// =============================================================================
int PIN_SCLK = GPU_DEFAULT_PIN_SCLK; // Default ESP32-S3: 12 (or 18 for classic ESP32)
int PIN_CS   = GPU_DEFAULT_PIN_CS;   // Default ESP32-S3: 10 (or 5 for classic ESP32)
int PIN_MOSI = GPU_DEFAULT_PIN_MOSI; // Default ESP32-S3: 11 (or 23 for classic ESP32)
int PIN_MISO = GPU_DEFAULT_PIN_MISO; // Default ESP32-S3: 13 (or 19 for classic ESP32)

// =============================================================================
// Palette Color Indices (from Master 256-Color Palette)
// =============================================================================
#define COL_BLACK        0
#define COL_DARK_BLUE    1
#define COL_FOREST_GREEN 2
#define COL_CYAN         3
#define COL_CRIMSON      4
#define COL_PURPLE       5
#define COL_BROWN        6
#define COL_LIGHT_GRAY   7
#define COL_DARK_GRAY    8
#define COL_BRIGHT_BLUE  9
#define COL_BRIGHT_GREEN 10
#define COL_BRIGHT_CYAN  11
#define COL_BRIGHT_RED   12
#define COL_MAGENTA      13
#define COL_GOLD         14
#define COL_WHITE        15
#define COL_HUD_NAVY     17  // Deep dark blue (0, 0, 51)
#define COL_WOOD_FLOOR   133 // Warm wood brown (153, 102, 51)
#define COL_DIRT_TRAIL   176 // Earthy tan (204, 153, 102)
#define COL_STONE_PLAZA  242 // Cobblestone slate gray

// =============================================================================
// Cast & Village Location Definitions
// =============================================================================
typedef enum {
    NPC_SHOPKEEPER = 0, // Dazai Osamu (General Store - NW)
    NPC_GUARD      = 1, // Escanor (Council Treasury - NE)
    NPC_FARMER     = 2, // Roronoa Zoro (Barn & Old Mill - SE)
    NPC_KID        = 3, // Naruto Uzumaki (Town Square Well - Center)
    NPC_OLD_MAN    = 4  // Master Roshi (Hermit Porch & Chapel - SW)
} npc_role_t;

typedef struct {
    const char* role_name;
    const char* anime_name;
    const char* district_name;
    int16_t     home_x;
    int16_t     home_y;
    int16_t     talk_x;      // Where Detective Zero stands to interrogate them
    int16_t     talk_y;
    bool        zero_face_left;
    uint16_t    spr_idle;
    uint16_t    spr_walk1;
    uint16_t    spr_walk2;
    uint16_t    spr_action;
    uint16_t    spr_portrait;
} npc_actor_t;

static const npc_actor_t NPC_CAST[AI_NUM_NPCS] = {
    {
        "SHOPKEEPER", "Dazai Osamu", "General Store (NW)",
        92, 72, 122, 82, true,
        SPRITE_ID_NPC_DAZAI_IDLE, SPRITE_ID_NPC_DAZAI_WALK1,
        SPRITE_ID_NPC_DAZAI_WALK2, SPRITE_ID_NPC_DAZAI_ACTION,
        SPRITE_ID_NPC_DAZAI_PORTRAIT
    },
    {
        "GUARD", "Captain Escanor", "Council Treasury (NE)",
        400, 84, 372, 92, false,
        SPRITE_ID_NPC_ESCANOR_IDLE, SPRITE_ID_NPC_ESCANOR_WALK1,
        SPRITE_ID_NPC_ESCANOR_WALK2, SPRITE_ID_NPC_ESCANOR_ACTION,
        SPRITE_ID_NPC_ESCANOR_PORTRAIT
    },
    {
        "FARMER", "Roronoa Zoro", "Barn & Old Mill (SE)",
        504, 276, 476, 282, false,
        SPRITE_ID_NPC_ZORO_IDLE, SPRITE_ID_NPC_ZORO_WALK1,
        SPRITE_ID_NPC_ZORO_WALK2, SPRITE_ID_NPC_ZORO_ACTION,
        SPRITE_ID_NPC_ZORO_PORTRAIT
    },
    {
        "KID", "Naruto Uzumaki", "Town Square Well (Center)",
        276, 190, 248, 194, false,
        SPRITE_ID_NPC_NARUTO_IDLE, SPRITE_ID_NPC_NARUTO_WALK1,
        SPRITE_ID_NPC_NARUTO_WALK2, SPRITE_ID_NPC_NARUTO_ACTION,
        SPRITE_ID_NPC_NARUTO_PORTRAIT
    },
    {
        "OLD_MAN", "Master Roshi", "Hermit Porch & Chapel (SW)",
        92, 286, 122, 290, true,
        SPRITE_ID_NPC_ROSHI_IDLE, SPRITE_ID_NPC_ROSHI_WALK1,
        SPRITE_ID_NPC_ROSHI_WALK2, SPRITE_ID_NPC_ROSHI_ACTION,
        SPRITE_ID_NPC_ROSHI_PORTRAIT
    }
};

static const char* const CULPRIT_NAMES[AI_NUM_CULPRITS] = {
    "SHOPKEEPER (Dazai Osamu)",
    "FARMER (Roronoa Zoro)",
    "GUARD (Captain Escanor)",
    "OLD_MAN (Master Roshi)"
};

// Map Culprit Enum (0..3) to NPC Role Index (0..4)
static const int CULPRIT_TO_NPC_IDX[AI_NUM_CULPRITS] = {
    NPC_SHOPKEEPER, // 0: SHOPKEEPER
    NPC_FARMER,     // 1: FARMER
    NPC_GUARD,      // 2: GUARD
    NPC_OLD_MAN     // 3: OLD_MAN
};

static const uint16_t CLUE_PROP_SPRITES[8] = {
    SPRITE_ID_PROP_LEDGER_RECEIPT, // Bit 0: Torn Ledger Receipt
    SPRITE_ID_PROP_CIDER_FLASK,    // Bit 1: Spiced Cider Flask
    SPRITE_ID_PROP_GUARD_BADGE,    // Bit 2: Brass Guard Crest Badge
    SPRITE_ID_PROP_WHEAT_STRAW,    // Bit 3: Wheat Straw Stalk
    SPRITE_ID_PROP_CANE_TIP,       // Bit 4: Broken Bamboo Cane Tip
    SPRITE_ID_PROP_ROPE_BANDAGE,   // Bit 5: Hemp Rope & Bandage
    SPRITE_ID_PROP_COIN_SACK,      // Bit 6: Council Tax Coin Sack
    SPRITE_ID_PROP_GOLD_CHEST      // Bit 7: Stolen Treasury Gold Chest
};

static const char* const CLUE_NAMES[8] = {
    "Torn Store Receipt",
    "Spiked Cider Flask",
    "Brass Guard Badge/Key",
    "Mill Cart Wheat Straw",
    "Broken Bamboo Cane Tip",
    "Hemp Rope & Bandages",
    "Council Tax Coin Sack",
    "Stolen Gold Chest"
};

// =============================================================================
// Live Game & Investigation State
// =============================================================================
static int      active_culprit   = 0;              // 0=SHOPKEEPER, 1=FARMER, 2=GUARD, 3=OLD_MAN
static int      target_npc       = NPC_SHOPKEEPER; // Currently targeted NPC (0..4)
static int      zero_x           = 248;            // Detective Zero X position
static int      zero_y           = 194;            // Detective Zero Y position
static bool     zero_facing_left = false;
static bool     zero_arrived     = false;
static bool     auto_tour_mode   = true;           // Auto-patrols until user sends Serial input
static uint32_t tour_pause_ticks = 0;
static int      tour_demo_step   = 0;

static uint8_t  npc_trust[AI_NUM_NPCS]       = {4, 4, 4, 5, 4}; // 0..5 hearts
static uint8_t  npc_stress[AI_NUM_NPCS]      = {20, 25, 20, 10, 15}; // 0..100 suspicion bar
static int      npc_last_intent[AI_NUM_NPCS] = {-1, -1, -1, -1, -1};
static uint8_t  discovered_clues_mask        = 0x03; // Start with 2 initial scene clues unlocked
static bool     case_solved                  = false;

static uint32_t frame_count = 0;
static char     serial_buf[192];
static size_t   serial_len  = 0;

// =============================================================================
// Asset Upload to FPGA SDRAM & CLUT
// =============================================================================
static void upload_assets_to_fpga(void) {
    Serial.println("[INIT] Uploading 256-Color Master Palette to FPGA BRAM CLUT...");
    gpu_load_palette_all(DEFAULT_GPU_PALETTE);

    Serial.printf("[INIT] Uploading %d 'Catch the Thief' Sprites (%d bytes) to FPGA SDRAM (0x100000)...\n",
                  TOTAL_SPRITES_COUNT, TOTAL_SPRITES_BYTES);

    // Upload each sprite slice with progress logging
    for (int i = 0; i < TOTAL_SPRITES_COUNT; i++) {
        const sprite_meta_t *meta = &SPRITE_METADATA[i];
        const uint8_t *data_ptr = &ALL_SPRITES_DATA[meta->sdram_offset];
        gpu_load_sprite_data(SDRAM_SPRITE_BASE_ADDR + meta->sdram_offset, data_ptr, meta->byte_length);
    }
    Serial.println("[INIT] All 51 character, tile, clue, and UI sprites cached in FPGA SDRAM!");
}

// =============================================================================
// Hardware-Accelerated Village World Renderer (640x392 Map Viewport)
// =============================================================================
static void draw_village_world(void) {
    // 1. Base Valley Grass Clear (Color 2: Forest Green)
    gpu_clear(COL_FOREST_GREEN);

    // 2. Main Village Road Network (Hardware Rectangles + Cobblestone/Dirt Sprite Accents)
    // Horizontal Central Cobblestone Road (x=24..560, y=196..228)
    gpu_draw_rect(24, 196, 536, 32, COL_DARK_GRAY);
    gpu_draw_rect(24, 200, 536, 24, COL_LIGHT_GRAY);
    // Vertical Crossroads (x=296..328, y=136..384)
    gpu_draw_rect(296, 136, 32, 248, COL_DARK_GRAY);
    gpu_draw_rect(300, 136, 24, 248, COL_LIGHT_GRAY);
    // North-West Path to Dazai's General Store
    gpu_draw_rect(112, 132, 24, 68, COL_LIGHT_GRAY);
    // South-West Path to Master Roshi's Porch
    gpu_draw_rect(112, 224, 24, 56, COL_LIGHT_GRAY);
    // Eastern Dirt Wagon Trail from Treasury to Zoro's Barn & Old Mill
    gpu_draw_rect(448, 136, 28, 168, COL_BROWN);
    gpu_draw_rect(452, 136, 20, 168, COL_DIRT_TRAIL);

    // Cobblestone & Dirt Sprite Texture Accents along the roads
    for (int x = 48; x <= 512; x += 64) {
        gpu_draw_sprite(x, 204, SPRITE_ID_TILE_COBBLESTONE, GPU_SPRITE_SIZE_16x16);
    }
    for (int y = 148; y <= 356; y += 52) {
        gpu_draw_sprite(304, y, SPRITE_ID_TILE_COBBLESTONE, GPU_SPRITE_SIZE_16x16);
    }
    for (int y = 152; y <= 264; y += 36) {
        gpu_draw_sprite(454, y, SPRITE_ID_TILE_DIRT_PATH, GPU_SPRITE_SIZE_16x16);
    }

    // Wildflower Meadow & Grass Tuft Tiles across the valley
    gpu_draw_sprite(208, 64,  SPRITE_ID_TILE_FLOWER_GRASS, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(224, 96,  SPRITE_ID_TILE_GRASS,        GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(208, 152, SPRITE_ID_TILE_FLOWER_GRASS, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(368, 160, SPRITE_ID_TILE_FLOWER_GRASS, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(216, 272, SPRITE_ID_TILE_FLOWER_GRASS, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(364, 312, SPRITE_ID_TILE_GRASS,        GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(236, 344, SPRITE_ID_TILE_FLOWER_GRASS, GPU_SPRITE_SIZE_16x16);

    // =========================================================================
    // DISTRICT 1 (NW): Dazai Osamu's General Store (x=24..184, y=20..132)
    // =========================================================================
    gpu_draw_rect(24, 20, 160, 112, COL_CRIMSON);      // Outer brick wall
    gpu_draw_rect(30, 36, 148, 90,  COL_WOOD_FLOOR);   // Wooden plank shop floor
    gpu_draw_rect(24, 20, 160, 16,  COL_BROWN);        // Shop roof beam
    gpu_draw_line(24, 20, 184, 20,  COL_GOLD);         // Gold sign trim
    // Storefront brick & wood plank sprite details
    gpu_draw_sprite(32,  20, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(160, 20, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(64,  56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(80,  56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(96,  56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(112, 56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    // Rainwater barrel outside shop (east wall)
    gpu_draw_sprite(164, 108, SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    // Clues in Dazai's Store: Hemp Rope & Bandages + Canvas Coin Sack
    gpu_draw_sprite(42,  84, SPRITE_ID_PROP_ROPE_BANDAGE, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(148, 84, SPRITE_ID_PROP_COIN_SACK,    GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // =========================================================================
    // DISTRICT 2 (NE): Council Treasury Vault & Escanor's Watchpost (x=272..576, y=16..136)
    // =========================================================================
    gpu_draw_rect(272, 16, 304, 120, COL_CRIMSON);     // Fortified brick perimeter
    gpu_draw_rect(280, 32, 288, 98,  COL_DARK_GRAY);   // Stone vault courtyard
    gpu_draw_rect(384, 20, 80,  56,  COL_HUD_NAVY);    // Inner Stronghold Chamber
    gpu_draw_line(384, 20, 464, 20,  COL_GOLD);
    gpu_draw_line(384, 76, 464, 76,  COL_GOLD);
    // Brick wall battlements & Double Iron Vault Doors
    gpu_draw_sprite(288, 16, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(352, 16, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(480, 16, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(544, 16, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(408, 28, SPRITE_ID_TILE_VAULT_DOOR, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(424, 28, SPRITE_ID_TILE_VAULT_DOOR, GPU_SPRITE_SIZE_16x16);
    // Escanor's Watchpost Desk (west side of courtyard)
    gpu_draw_rect(300, 76, 48, 24, COL_BROWN);
    gpu_draw_sprite(316, 80, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    // Clues at the Treasury: Spiced Cider Flask, Brass Guard Badge, Gold Chest
    gpu_draw_sprite(336, 82,  SPRITE_ID_PROP_CIDER_FLASK, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(448, 104, SPRITE_ID_PROP_GUARD_BADGE, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(416, 52,  SPRITE_ID_PROP_GOLD_CHEST,  GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // =========================================================================
    // DISTRICT 3 (CENTER): Village Crossroads & Town Well (x=256..368, y=168..252)
    // =========================================================================
    gpu_draw_rect(268, 176, 88, 68, COL_DARK_GRAY);
    // Central Stone Well
    gpu_draw_rect(300, 192, 28, 28, COL_LIGHT_GRAY);
    gpu_draw_sprite(306, 198, SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    // Clue near Town Well: Torn Store Ledger Receipt
    gpu_draw_sprite(336, 180, SPRITE_ID_PROP_LEDGER_RECEIPT, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // =========================================================================
    // DISTRICT 4 (SW): Master Roshi's Porch & Old Chapel Ruins (x=24..188, y=256..376)
    // =========================================================================
    // Master Roshi's Kame Porch
    gpu_draw_rect(24, 260, 108, 88, COL_BROWN);
    gpu_draw_rect(30, 268, 96,  74, COL_WOOD_FLOOR);
    gpu_draw_sprite(40, 272, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(72, 272, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    // Old Chapel Stone Ruins & Crypt (east of porch)
    gpu_draw_rect(140, 276, 56, 88, COL_DARK_GRAY);
    gpu_draw_sprite(148, 280, SPRITE_ID_TILE_BRICK_WALL,  GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(168, 280, SPRITE_ID_TILE_COBBLESTONE, GPU_SPRITE_SIZE_16x16);
    // Clue near Chapel Gravel: Broken Bamboo Cane Tip
    gpu_draw_sprite(156, 336, SPRITE_ID_PROP_CANE_TIP, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // =========================================================================
    // DISTRICT 5 (SE): Zoro's Barn, Farmhouse & Old Mill River (x=408..624, y=244..380)
    // =========================================================================
    // Flowing Mill River on the eastern edge (x=572..624, y=156..384)
    gpu_draw_rect(572, 156, 52, 228, COL_DARK_BLUE);
    gpu_draw_rect(578, 156, 40, 228, COL_BRIGHT_BLUE);
    for (int wy = 168; wy <= 360; wy += 48) {
        gpu_draw_sprite(588, wy + ((frame_count >> 2) & 0x07), SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    }
    // Zoro's Barn & Old Mill Granary
    gpu_draw_rect(412, 248, 148, 120, COL_BROWN);
    gpu_draw_rect(420, 260, 132, 100, COL_WOOD_FLOOR);
    gpu_draw_sprite(428, 248, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(524, 248, SPRITE_ID_TILE_BRICK_WALL, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(480, 264, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    // Clues at Barn & Mill: 32x32 Handcart, Wheat Straw Stalk, Hidden Gold Chest
    gpu_draw_sprite(432, 284, SPRITE_ID_PROP_HANDCART,    GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(424, 264, SPRITE_ID_PROP_WHEAT_STRAW, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(532, 332, SPRITE_ID_PROP_GOLD_CHEST,  GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(512, 332, SPRITE_ID_PROP_COIN_SACK,   GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
}

// =============================================================================
// Render All 5 Anime NPCs + Player Detective Zero (Lelouch)
// =============================================================================
static void update_and_draw_characters(void) {
    // 1. Move Detective Zero smoothly toward the active target NPC's talk position
    int16_t dest_x = NPC_CAST[target_npc].talk_x;
    int16_t dest_y = NPC_CAST[target_npc].talk_y;

    int dx = dest_x - zero_x;
    int dy = dest_y - zero_y;
    int speed = 4;

    if (abs(dx) <= speed && abs(dy) <= speed) {
        zero_x = dest_x;
        zero_y = dest_y;
        zero_facing_left = NPC_CAST[target_npc].zero_face_left;
        zero_arrived = true;
    } else {
        zero_arrived = false;
        if (abs(dx) > speed) {
            zero_x += (dx > 0) ? speed : -speed;
            zero_facing_left = (dx < 0);
        } else {
            zero_x = dest_x;
        }
        if (abs(dy) > speed) {
            zero_y += (dy > 0) ? speed : -speed;
        } else {
            zero_y = dest_y;
        }
    }

    // 2. Draw Pulsing Golden Target Highlight Under Active NPC
    int16_t tx = NPC_CAST[target_npc].home_x;
    int16_t ty = NPC_CAST[target_npc].home_y;
    uint8_t ring_col = ((frame_count >> 2) & 1) ? COL_GOLD : COL_BRIGHT_CYAN;
    gpu_draw_line(tx - 4,  ty - 4,  tx + 20, ty - 4,  ring_col);
    gpu_draw_line(tx + 20, ty - 4,  tx + 20, ty + 34, ring_col);
    gpu_draw_line(tx + 20, ty + 34, tx - 4,  ty + 34, ring_col);
    gpu_draw_line(tx - 4,  ty + 34, tx - 4,  ty - 4,  ring_col);

    // 3. Draw All 5 Suspects with Idle/Walk/Action Animations
    int anim_phase = (frame_count >> 3) & 3; // 0, 1, 2, 3
    for (int i = 0; i < AI_NUM_NPCS; i++) {
        int16_t nx = NPC_CAST[i].home_x;
        int16_t ny = NPC_CAST[i].home_y;
        uint16_t spr_id = NPC_CAST[i].spr_idle;
        uint8_t flags = GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN;

        if (i == target_npc && zero_arrived) {
            // Active interrogation: NPC strikes their signature Action pose or Idle!
            spr_id = ((frame_count >> 4) & 1) ? NPC_CAST[i].spr_action : NPC_CAST[i].spr_idle;
            if (!NPC_CAST[i].zero_face_left) {
                flags |= GPU_SPRITE_FLIP_X; // Face Detective Zero
            }
        } else {
            // Subtle patrol / breathing animation in their district
            int sway = ((frame_count + i * 11) >> 3) & 7;
            int offset_x = (sway < 4) ? sway : (7 - sway);
            nx += offset_x;
            if (anim_phase == 1) spr_id = NPC_CAST[i].spr_walk1;
            else if (anim_phase == 3) spr_id = NPC_CAST[i].spr_walk2;
            if (sway >= 4) flags |= GPU_SPRITE_FLIP_X;
        }

        gpu_draw_sprite(nx, ny, spr_id, flags);
    }

    // 4. Draw Detective Zero (Lelouch vi Britannia)
    uint16_t zero_spr = SPRITE_ID_HERO_ZERO_IDLE;
    if (!zero_arrived) {
        zero_spr = ((frame_count >> 2) & 1) ? SPRITE_ID_HERO_ZERO_WALK1 : SPRITE_ID_HERO_ZERO_WALK2;
    } else {
        // Strike dramatic Geass Deduction Pose while interrogating!
        zero_spr = ((frame_count >> 4) & 1) ? SPRITE_ID_HERO_ZERO_ACTION : SPRITE_ID_HERO_ZERO_IDLE;
    }

    uint8_t zero_flags = GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN;
    if (zero_facing_left) {
        zero_flags |= GPU_SPRITE_FLIP_X;
    }
    gpu_draw_sprite(zero_x, zero_y, zero_spr, zero_flags);
}

// =============================================================================
// Bottom Investigation & Interrogation HUD (y = 392..479)
// =============================================================================
static void draw_investigation_hud(void) {
    // 1. Main HUD Panel Background (Dark Navy with Gold & White Borders)
    gpu_draw_rect(0, 392, 640, 88, COL_HUD_NAVY);
    gpu_draw_line(0, 392, 639, 392, COL_GOLD);
    gpu_draw_line(0, 394, 639, 394, COL_WHITE);
    gpu_draw_line(0, 478, 639, 478, COL_GOLD);

    // Corner UI Ornaments
    gpu_draw_sprite(2,   396, SPRITE_ID_UI_DIALOGUE_BORDER, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(622, 396, SPRITE_ID_UI_DIALOGUE_BORDER, GPU_SPRITE_SIZE_16x16);

    // 2. Left Slot: Detective Zero 32x32 Portrait & Magnifying Glass
    gpu_draw_rect(24, 402, 40, 40, COL_GOLD);
    gpu_draw_rect(26, 404, 36, 36, COL_BLACK);
    gpu_draw_sprite(28, 406, SPRITE_ID_HERO_ZERO_PORTRAIT, GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(36, 448, SPRITE_ID_UI_MAGNIFIER,       GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // 3. Center-Left Slot: Active Suspect 32x32 Portrait + Trust Hearts + Suspicion Meter
    gpu_draw_rect(76, 402, 40, 40, case_solved ? COL_BRIGHT_GREEN : COL_BRIGHT_CYAN);
    gpu_draw_rect(78, 404, 36, 36, COL_BLACK);
    gpu_draw_sprite(80, 406, NPC_CAST[target_npc].spr_portrait, GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);

    // Suspect Selection Indicator Tabs (5 tabs for the 5 NPCs)
    for (int i = 0; i < AI_NUM_NPCS; i++) {
        int tab_x = 126 + i * 38;
        uint8_t tab_col = (i == target_npc) ? COL_GOLD : COL_DARK_GRAY;
        gpu_draw_rect(tab_x, 402, 32, 10, tab_col);
    }

    // 5 Trust Hearts for Active Suspect (Full vs Empty)
    uint8_t trust = npc_trust[target_npc];
    for (int h = 0; h < 5; h++) {
        uint16_t heart_spr = (h < trust) ? SPRITE_ID_UI_HEART_FULL : SPRITE_ID_UI_HEART_EMPTY;
        gpu_draw_sprite(126 + h * 20, 418, heart_spr, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    }

    // Stress / Suspicion Progress Bar (x=126..316, y=442..456)
    gpu_draw_rect(126, 442, 190, 14, COL_DARK_GRAY);
    int stress_w = (npc_stress[target_npc] * 186) / 100;
    if (stress_w > 186) stress_w = 186;
    uint8_t stress_col = (npc_stress[target_npc] >= 75) ? COL_BRIGHT_RED :
                         (npc_stress[target_npc] >= 45) ? COL_GOLD : COL_BRIGHT_GREEN;
    if (stress_w > 0) {
        gpu_draw_rect(128, 444, stress_w, 10, stress_col);
    }

    // Case Solved Banner Indicator
    if (case_solved) {
        gpu_draw_rect(126, 460, 190, 12, COL_BRIGHT_GREEN);
    } else {
        gpu_draw_rect(126, 460, 190, 12, COL_DARK_BLUE);
    }

    // 4. Right Slot: Physical Evidence Locker (8 Clue Slots at x=336..616)
    gpu_draw_rect(332, 402, 284, 68, COL_BLACK);
    gpu_draw_line(332, 402, 616, 402, COL_GOLD);
    gpu_draw_line(332, 470, 616, 470, COL_GOLD);

    for (int c = 0; c < 8; c++) {
        int cx = 340 + c * 34;
        int cy = 420;
        bool unlocked = (discovered_clues_mask & (1 << c)) != 0;

        // Draw slot frame (Gold if discovered, Dark Gray if locked)
        gpu_draw_rect(cx - 2, cy - 2, 20, 20, unlocked ? COL_GOLD : COL_DARK_GRAY);
        gpu_draw_rect(cx,     cy,     16, 16, unlocked ? COL_HUD_NAVY : COL_BLACK);

        if (unlocked) {
            gpu_draw_sprite(cx, cy, CLUE_PROP_SPRITES[c], GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
        }
    }
}

// =============================================================================
// AI Interrogation & Serial Command Engine
// =============================================================================
static void print_game_status(void) {
    Serial.println("\n======================================================================");
    Serial.println("   CATCH THE THIEF — ANIME DETECTIVE CONSOLE (FPGA GPU + EDGE AI)     ");
    Serial.println("======================================================================");
    Serial.printf(" Active Scenario Culprit : %s\n", CULPRIT_NAMES[active_culprit]);
    Serial.printf(" Interrogating Suspect   : [%s] %s @ %s\n",
                  NPC_CAST[target_npc].role_name,
                  NPC_CAST[target_npc].anime_name,
                  NPC_CAST[target_npc].district_name);
    Serial.printf(" Suspect Trust / Stress  : %u/5 Hearts | %u%% Suspicion\n",
                  npc_trust[target_npc], npc_stress[target_npc]);
    Serial.print(" Unlocked Clues          : ");
    int cnt = 0;
    for (int i = 0; i < 8; i++) {
        if (discovered_clues_mask & (1 << i)) {
            if (cnt > 0) Serial.print(", ");
            Serial.print(CLUE_NAMES[i]);
            cnt++;
        }
    }
    if (cnt == 0) Serial.print("None yet");
    Serial.println("\n----------------------------------------------------------------------");
    Serial.println(" Commands: /shopkeeper, /guard, /farmer, /kid, /old_man, /tour");
    Serial.println("           /culprit <role>, /accuse <role>, or ask ANY question!");
    Serial.println("======================================================================\n");
}

static int parse_npc_name(const char* s) {
    if (ai_has_sub(s, "shop") || ai_has_sub(s, "dazai") || strcmp(s, "1") == 0) return NPC_SHOPKEEPER;
    if (ai_has_sub(s, "guard") || ai_has_sub(s, "escanor") || strcmp(s, "2") == 0) return NPC_GUARD;
    if (ai_has_sub(s, "farm") || ai_has_sub(s, "zoro") || strcmp(s, "3") == 0) return NPC_FARMER;
    if (ai_has_sub(s, "kid") || ai_has_sub(s, "naruto") || strcmp(s, "4") == 0) return NPC_KID;
    if (ai_has_sub(s, "old") || ai_has_sub(s, "roshi") || strcmp(s, "5") == 0) return NPC_OLD_MAN;
    return -1;
}

static void interrogate_active_npc(const char* player_query) {
    // Check if the player is asking where to find another character
    if (ai_has_sub(player_query, "find the guard") || ai_has_sub(player_query, "where is the guard") || ai_has_sub(player_query, "where is escanor")) {
        target_npc = NPC_GUARD;
        Serial.println("[NAV] Detective Zero is heading to the Council Treasury (NE) to question Captain Escanor!");
        return;
    }
    if (ai_has_sub(player_query, "find the shopkeeper") || ai_has_sub(player_query, "where is dazai")) {
        target_npc = NPC_SHOPKEEPER;
        Serial.println("[NAV] Detective Zero is heading to the General Store (NW) to question Dazai Osamu!");
        return;
    }
    if (ai_has_sub(player_query, "find the farmer") || ai_has_sub(player_query, "where is zoro")) {
        target_npc = NPC_FARMER;
        Serial.println("[NAV] Detective Zero is heading to the Barn & Old Mill (SE) to question Roronoa Zoro!");
        return;
    }
    if (ai_has_sub(player_query, "find the kid") || ai_has_sub(player_query, "where is naruto")) {
        target_npc = NPC_KID;
        Serial.println("[NAV] Detective Zero is heading to the Town Well (Center) to question Naruto Uzumaki!");
        return;
    }
    if (ai_has_sub(player_query, "find the old man") || ai_has_sub(player_query, "where is roshi")) {
        target_npc = NPC_OLD_MAN;
        Serial.println("[NAV] Detective Zero is heading to the Hermit Porch (SW) to question Master Roshi!");
        return;
    }

    int intent_idx = ai_match_intent(player_query, npc_last_intent[target_npc]);
    npc_last_intent[target_npc] = intent_idx;

    const char* response = AI_DIALOGUE_MATRIX[active_culprit][target_npc][intent_idx];

    // Update trust & stress based on question type
    if (intent_idx >= 29 && intent_idx <= 31) {
        // Accusation / pressing
        if (npc_trust[target_npc] > 1) npc_trust[target_npc]--;
        if (npc_stress[target_npc] <= 80) npc_stress[target_npc] += 20;
    } else if (intent_idx <= 2 || intent_idx == 33) {
        // Polite greeting / rapport
        if (npc_trust[target_npc] < 5) npc_trust[target_npc]++;
    } else {
        // Standard investigative probing
        if (npc_stress[target_npc] <= 90) npc_stress[target_npc] += 8;
    }

    // Unlock physical clue in HUD if this intent reveals evidence
    int clue_bit = ai_intent_clue_bit(intent_idx);
    if (clue_bit >= 0 && !(discovered_clues_mask & (1 << clue_bit))) {
        discovered_clues_mask |= (1 << clue_bit);
        Serial.printf("  [CLUE UNLOCKED ON HDMI HUD!] -> %s\n", CLUE_NAMES[clue_bit]);
    }

    Serial.printf("\n[ZERO -> %s]: \"%s\"\n", NPC_CAST[target_npc].anime_name, player_query);
    Serial.printf("[%s (%s)]: \"%s\"\n\n",
                  NPC_CAST[target_npc].role_name,
                  NPC_CAST[target_npc].anime_name,
                  response);
}

static void handle_serial_command(const char* line) {
    while (*line == ' ' || *line == '\t') line++;
    if (*line == '\0') return;

    // Protocol sync hook for PC Python nanoGPT Bridge (ai/play_game.py):
    // Format: AI_SYNC:<npc_idx>:<trust>:<stress>:<clue_mask>:<culprit_idx>
    if (strncmp(line, "AI_SYNC:", 8) == 0) {
        int n_idx = 0, tr = 4, st = 25, cm = 0, culp = 0;
        if (sscanf(line + 8, "%d:%d:%d:%d:%d", &n_idx, &tr, &st, &cm, &culp) >= 4) {
            auto_tour_mode = false;
            if (n_idx >= 0 && n_idx < AI_NUM_NPCS) {
                target_npc = n_idx;
                npc_trust[n_idx] = (uint8_t)tr;
                npc_stress[n_idx] = (uint8_t)st;
            }
            discovered_clues_mask = (uint8_t)cm;
            if (culp >= 0 && culp < AI_NUM_CULPRITS) active_culprit = culp;
            Serial.printf("[BRIDGE] Synced HUD -> NPC=%s, Trust=%d, Stress=%d%%, Clues=0x%02X\n",
                          NPC_CAST[target_npc].role_name, tr, st, discovered_clues_mask);
        }
        return;
    }

    if (line[0] == '/') {
        const char* cmd = line + 1;
        if (strncmp(cmd, "help", 4) == 0 || strncmp(cmd, "status", 6) == 0) {
            print_game_status();
            return;
        }
        if (strncmp(cmd, "tour", 4) == 0 || strncmp(cmd, "auto", 4) == 0) {
            auto_tour_mode = true;
            Serial.println("[MODE] Autonomous Village Patrol & Demo Interrogation ENABLED.");
            return;
        }
        if (strncmp(cmd, "culprit", 7) == 0 || strncmp(cmd, "newgame", 7) == 0) {
            const char* arg = cmd + 7;
            while (*arg == ' ') arg++;
            if (ai_has_sub(arg, "shop") || ai_has_sub(arg, "dazai")) active_culprit = 0;
            else if (ai_has_sub(arg, "farm") || ai_has_sub(arg, "zoro")) active_culprit = 1;
            else if (ai_has_sub(arg, "guard") || ai_has_sub(arg, "escanor")) active_culprit = 2;
            else if (ai_has_sub(arg, "old") || ai_has_sub(arg, "roshi")) active_culprit = 3;
            else active_culprit = (active_culprit + 1) % AI_NUM_CULPRITS;

            case_solved = false;
            discovered_clues_mask = 0x01;
            for (int i = 0; i < AI_NUM_NPCS; i++) {
                npc_trust[i] = 4;
                npc_stress[i] = 15;
                npc_last_intent[i] = -1;
            }
            Serial.printf("\n[NEW MYSTERY] Scenario Reset! Active Culprit = %s\n", CULPRIT_NAMES[active_culprit]);
            return;
        }
        if (strncmp(cmd, "accuse", 6) == 0) {
            auto_tour_mode = false;
            const char* arg = cmd + 6;
            while (*arg == ' ') arg++;
            int accused_npc = (*arg != '\0') ? parse_npc_name(arg) : target_npc;
            if (accused_npc < 0) accused_npc = target_npc;
            target_npc = accused_npc;

            int true_culprit_npc = CULPRIT_TO_NPC_IDX[active_culprit];
            Serial.println("\n**********************************************************************");
            if (accused_npc == true_culprit_npc) {
                case_solved = true;
                discovered_clues_mask = 0xFF; // Reveal all clues on HUD!
                npc_stress[accused_npc] = 100;
                Serial.printf(" [CASE SOLVED!] Detective Zero indicts %s (%s)!\n",
                              NPC_CAST[accused_npc].role_name, NPC_CAST[accused_npc].anime_name);
                Serial.printf(" Confession: \"%s\"\n",
                              AI_DIALOGUE_MATRIX[active_culprit][accused_npc][31]);
            } else {
                Serial.printf(" [FALSE ACCUSATION!] %s (%s) is NOT the mastermind in this scenario!\n",
                              NPC_CAST[accused_npc].role_name, NPC_CAST[accused_npc].anime_name);
                Serial.println(" Keep gathering clues and interrogating the suspects!");
            }
            Serial.println("**********************************************************************\n");
            return;
        }

        int npc_sel = parse_npc_name(cmd);
        if (npc_sel >= 0) {
            auto_tour_mode = false;
            target_npc = npc_sel;
            Serial.printf("\n[MOVE] Detective Zero is walking to %s (%s) at %s...\n",
                          NPC_CAST[target_npc].anime_name,
                          NPC_CAST[target_npc].role_name,
                          NPC_CAST[target_npc].district_name);
            return;
        }
    }

    // Check single-digit shortcuts '1'..'5'
    int quick_npc = parse_npc_name(line);
    if (quick_npc >= 0 && strlen(line) <= 2) {
        auto_tour_mode = false;
        target_npc = quick_npc;
        Serial.printf("\n[MOVE] Switching interrogation target to %s (%s)...\n",
                      NPC_CAST[target_npc].anime_name, NPC_CAST[target_npc].role_name);
        return;
    }

    // Otherwise, treat input as a natural-language question to the active NPC!
    auto_tour_mode = false;
    interrogate_active_npc(line);
}

static void poll_serial_input(void) {
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_len > 0) {
                serial_buf[serial_len] = '\0';
                handle_serial_command(serial_buf);
                serial_len = 0;
            }
        } else if (serial_len < sizeof(serial_buf) - 1) {
            serial_buf[serial_len++] = c;
        }
    }
}

// =============================================================================
// Autonomous Village Patrol & Demo Interrogation (when auto_tour_mode == true)
// =============================================================================
static const char* const DEMO_TOUR_QUESTIONS[] = {
    "where were you last night",
    "did you see anything unusual",
    "how did they enter the vault",
    "who bought the canvas sacks",
    "who do you suspect"
};

static void update_auto_tour(void) {
    if (!auto_tour_mode) return;

    if (zero_arrived) {
        tour_pause_ticks++;
        if (tour_pause_ticks == 25) {
            // Ask a demo question automatically so the user sees live AI dialogue in Serial & HUD updates!
            const char* q = DEMO_TOUR_QUESTIONS[tour_demo_step % 5];
            tour_demo_step++;
            interrogate_active_npc(q);
        } else if (tour_pause_ticks >= 90) {
            tour_pause_ticks = 0;
            target_npc = (target_npc + 1) % AI_NUM_NPCS;
        }
    }
}

// =============================================================================
// Arduino Setup & 60 FPS Main Render Loop
// =============================================================================
void setup() {
    Serial.begin(115200);
    delay(1500);

    Serial.println("\n======================================================================");
    Serial.println("   CUSTOM FPGA GPU — 'CATCH THE THIEF' ANIME RPG & AI INTERROGATOR   ");
    Serial.println("======================================================================");

    // Initialize SPI bus to Tang Nano 20K (4 MHz for rock-solid sampling on 25.2 MHz FPGA clock)
    int ret = gpu_init(PIN_SCLK, PIN_CS, PIN_MOSI, PIN_MISO, 4000000);
    if (ret != 0) {
        Serial.println("[ERROR] Failed to initialize GPU SPI bus!");
        while (1) delay(1000);
    }

    uint8_t status = gpu_nop();
    Serial.printf("[INIT] GPU Telemetry Status: 0x%02X (Clear=%d, Sprite=%d, Line=%d, Rect=%d, Buf=%d)\n",
                  status,
                  (status & GPU_STATUS_CLEAR_BUSY) != 0,
                  (status & GPU_STATUS_SPRITE_BUSY) != 0,
                  (status & GPU_STATUS_LINE_BUSY) != 0,
                  (status & GPU_STATUS_RECT_BUSY) != 0,
                  (status & GPU_STATUS_FRONT_BUF) != 0);

    // Upload 256-color palette and all 51 sprites (8-bar test pattern remains visible during upload)
    upload_assets_to_fpga();

    Serial.println("[INIT] Displaying FPGA 8-bar color test pattern for 2 seconds...");
    delay(2000);

    print_game_status();
}

void loop() {
    // 1. Poll interactive Serial commands / questions / PC AI bridge
    poll_serial_input();

    // 2. Step autonomous patrol tour if user hasn't taken manual control
    update_auto_tour();

    // 3. Render Complete 5-District Village World into Active Back Buffer
    draw_village_world();

    // 4. Update & Render All 5 Animated Suspects + Detective Zero
    update_and_draw_characters();

    // 5. Render Bottom Investigation HUD (Portraits, Trust Hearts, Stress Bar, 8 Clue Slots)
    draw_investigation_hud();

    // 6. Tear-Free Double-Buffer Page Flip Synchronized to VSYNC
    gpu_swap_buffers();

    frame_count++;
    if (frame_count <= 5 || frame_count % 120 == 0) {
        uint8_t st = gpu_get_status();
        Serial.printf("[GPU] Frame %lu | FrontBuf=%d | Zero=(%d,%d) -> %s | Clues=0x%02X | Status=0x%02X\n",
                      (unsigned long)frame_count,
                      (st & GPU_STATUS_FRONT_BUF) != 0,
                      zero_x, zero_y,
                      NPC_CAST[target_npc].anime_name,
                      discovered_clues_mask,
                      st);
    }

    delay(1);
}
