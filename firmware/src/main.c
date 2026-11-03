/**
 * @file main.c
 * @brief Custom FPGA-Based GPU 60 FPS "Catch the Thief" Interactive Game & AI Engine
 * @project Custom FPGA-Based GPU — Woxsen University
 * @target ESP32-S3 -> Gowin GW2AR-18C Tang Nano 20K
 *
 * Demonstrates the full capabilities of the custom GPU:
 * 1. High-speed SPI link initialization (4 MHz)
 * 2. Uploading 256-color palette to FPGA BRAM CLUT
 * 3. Streaming all 51 "Catch the Thief" sprites (24,576 bytes) into FPGA SDRAM (0x100000+)
 * 4. Rendering the 5-district village world (Dazai's Store, Council Treasury, Town Well,
 *    Master Roshi's Porch & Chapel Ruins, Zoro's Barn & Old Mill River)
 * 5. Animating all 6 anime characters (Detective Zero + 5 suspects) with hardware Flip-X
 * 6. Rendering the bottom Investigation HUD (32x32 portraits, trust hearts, 8 clue slots)
 * 7. Tear-free 60 FPS double-buffering page flip synchronized to VSYNC
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "gpu_commands.h"
#include "sprites.h"
#include "ai_dialogue_table.h"

#if defined(ESP_PLATFORM)
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#define DELAY_MS(ms) vTaskDelay(pdMS_TO_TICKS(ms))
#else
#define DELAY_MS(ms)
#endif

#define COL_BLACK        0
#define COL_DARK_BLUE    1
#define COL_FOREST_GREEN 2
#define COL_CRIMSON      4
#define COL_BROWN        6
#define COL_LIGHT_GRAY   7
#define COL_DARK_GRAY    8
#define COL_BRIGHT_BLUE  9
#define COL_BRIGHT_GREEN 10
#define COL_BRIGHT_CYAN  11
#define COL_BRIGHT_RED   12
#define COL_GOLD         14
#define COL_WHITE        15
#define COL_HUD_NAVY     17
#define COL_WOOD_FLOOR   133
#define COL_DIRT_TRAIL   176

typedef struct {
    const char* role_name;
    const char* anime_name;
    int16_t     home_x;
    int16_t     home_y;
    int16_t     talk_x;
    int16_t     talk_y;
    bool        zero_face_left;
    uint16_t    spr_idle;
    uint16_t    spr_walk1;
    uint16_t    spr_walk2;
    uint16_t    spr_action;
    uint16_t    spr_portrait;
} npc_actor_t;

static const npc_actor_t NPC_CAST[AI_NUM_NPCS] = {
    {"SHOPKEEPER", "Dazai Osamu",     92,  72,  122, 82,  true,
     SPRITE_ID_NPC_DAZAI_IDLE, SPRITE_ID_NPC_DAZAI_WALK1, SPRITE_ID_NPC_DAZAI_WALK2, SPRITE_ID_NPC_DAZAI_ACTION, SPRITE_ID_NPC_DAZAI_PORTRAIT},
    {"GUARD",      "Captain Escanor", 400, 84,  372, 92,  false,
     SPRITE_ID_NPC_ESCANOR_IDLE, SPRITE_ID_NPC_ESCANOR_WALK1, SPRITE_ID_NPC_ESCANOR_WALK2, SPRITE_ID_NPC_ESCANOR_ACTION, SPRITE_ID_NPC_ESCANOR_PORTRAIT},
    {"FARMER",     "Roronoa Zoro",    504, 276, 476, 282, false,
     SPRITE_ID_NPC_ZORO_IDLE, SPRITE_ID_NPC_ZORO_WALK1, SPRITE_ID_NPC_ZORO_WALK2, SPRITE_ID_NPC_ZORO_ACTION, SPRITE_ID_NPC_ZORO_PORTRAIT},
    {"KID",        "Naruto Uzumaki",  276, 190, 248, 194, false,
     SPRITE_ID_NPC_NARUTO_IDLE, SPRITE_ID_NPC_NARUTO_WALK1, SPRITE_ID_NPC_NARUTO_WALK2, SPRITE_ID_NPC_NARUTO_ACTION, SPRITE_ID_NPC_NARUTO_PORTRAIT},
    {"OLD_MAN",    "Master Roshi",    92,  286, 122, 290, true,
     SPRITE_ID_NPC_ROSHI_IDLE, SPRITE_ID_NPC_ROSHI_WALK1, SPRITE_ID_NPC_ROSHI_WALK2, SPRITE_ID_NPC_ROSHI_ACTION, SPRITE_ID_NPC_ROSHI_PORTRAIT}
};

static const uint16_t CLUE_PROP_SPRITES[8] = {
    SPRITE_ID_PROP_LEDGER_RECEIPT,
    SPRITE_ID_PROP_CIDER_FLASK,
    SPRITE_ID_PROP_GUARD_BADGE,
    SPRITE_ID_PROP_WHEAT_STRAW,
    SPRITE_ID_PROP_CANE_TIP,
    SPRITE_ID_PROP_ROPE_BANDAGE,
    SPRITE_ID_PROP_COIN_SACK,
    SPRITE_ID_PROP_GOLD_CHEST
};

static void upload_assets_to_fpga(void) {
    printf("[INIT] Uploading 256-Color Palette to FPGA CLUT...\n");
    gpu_load_palette_all(DEFAULT_GPU_PALETTE);

    printf("[INIT] Uploading %d Sprites (%d bytes) to FPGA SDRAM (Base 0x100000)...\n",
           TOTAL_SPRITES_COUNT, TOTAL_SPRITES_BYTES);
    for (int i = 0; i < TOTAL_SPRITES_COUNT; i++) {
        const sprite_meta_t *meta = &SPRITE_METADATA[i];
        const uint8_t *data_ptr = &ALL_SPRITES_DATA[meta->sdram_offset];
        gpu_load_sprite_data(SDRAM_SPRITE_BASE_ADDR + meta->sdram_offset, data_ptr, meta->byte_length);
    }
    printf("[INIT] All 51 sprites cached in FPGA SDRAM!\n");
}

static void draw_village_world(uint32_t frame_count) {
    gpu_clear(COL_FOREST_GREEN);

    // Roads
    gpu_draw_rect(24, 196, 536, 32, COL_DARK_GRAY);
    gpu_draw_rect(24, 200, 536, 24, COL_LIGHT_GRAY);
    gpu_draw_rect(296, 136, 32, 248, COL_DARK_GRAY);
    gpu_draw_rect(300, 136, 24, 248, COL_LIGHT_GRAY);
    gpu_draw_rect(112, 132, 24, 68, COL_LIGHT_GRAY);
    gpu_draw_rect(112, 224, 24, 56, COL_LIGHT_GRAY);
    gpu_draw_rect(448, 136, 28, 168, COL_BROWN);
    gpu_draw_rect(452, 136, 20, 168, COL_DIRT_TRAIL);

    for (int x = 48; x <= 512; x += 64) {
        gpu_draw_sprite(x, 204, SPRITE_ID_TILE_COBBLESTONE, GPU_SPRITE_SIZE_16x16);
    }
    for (int y = 148; y <= 356; y += 52) {
        gpu_draw_sprite(304, y, SPRITE_ID_TILE_COBBLESTONE, GPU_SPRITE_SIZE_16x16);
    }
    for (int y = 152; y <= 264; y += 36) {
        gpu_draw_sprite(454, y, SPRITE_ID_TILE_DIRT_PATH, GPU_SPRITE_SIZE_16x16);
    }

    // NW: Dazai's General Store
    gpu_draw_rect(24, 20, 160, 112, COL_CRIMSON);
    gpu_draw_rect(30, 36, 148, 90,  COL_WOOD_FLOOR);
    gpu_draw_rect(24, 20, 160, 16,  COL_BROWN);
    gpu_draw_sprite(64,  56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(96,  56, SPRITE_ID_TILE_WOOD_PLANK, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(164, 108, SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(42,  84, SPRITE_ID_PROP_ROPE_BANDAGE, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(148, 84, SPRITE_ID_PROP_COIN_SACK,    GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // NE: Council Treasury & Escanor's Watchpost
    gpu_draw_rect(272, 16, 304, 120, COL_CRIMSON);
    gpu_draw_rect(280, 32, 288, 98,  COL_DARK_GRAY);
    gpu_draw_rect(384, 20, 80,  56,  COL_HUD_NAVY);
    gpu_draw_sprite(408, 28, SPRITE_ID_TILE_VAULT_DOOR, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(424, 28, SPRITE_ID_TILE_VAULT_DOOR, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(336, 82,  SPRITE_ID_PROP_CIDER_FLASK, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(448, 104, SPRITE_ID_PROP_GUARD_BADGE, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(416, 52,  SPRITE_ID_PROP_GOLD_CHEST,  GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // Center: Town Square & Well
    gpu_draw_rect(268, 176, 88, 68, COL_DARK_GRAY);
    gpu_draw_rect(300, 192, 28, 28, COL_LIGHT_GRAY);
    gpu_draw_sprite(306, 198, SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    gpu_draw_sprite(336, 180, SPRITE_ID_PROP_LEDGER_RECEIPT, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // SW: Master Roshi's Porch & Chapel Ruins
    gpu_draw_rect(24, 260, 108, 88, COL_BROWN);
    gpu_draw_rect(30, 268, 96,  74, COL_WOOD_FLOOR);
    gpu_draw_rect(140, 276, 56, 88, COL_DARK_GRAY);
    gpu_draw_sprite(156, 336, SPRITE_ID_PROP_CANE_TIP, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);

    // SE: Zoro's Barn & Old Mill River
    gpu_draw_rect(572, 156, 52, 228, COL_DARK_BLUE);
    gpu_draw_rect(578, 156, 40, 228, COL_BRIGHT_BLUE);
    for (int wy = 168; wy <= 360; wy += 48) {
        gpu_draw_sprite(588, wy + ((frame_count >> 2) & 0x07), SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
    }
    gpu_draw_rect(412, 248, 148, 120, COL_BROWN);
    gpu_draw_rect(420, 260, 132, 100, COL_WOOD_FLOOR);
    gpu_draw_sprite(432, 284, SPRITE_ID_PROP_HANDCART,    GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(424, 264, SPRITE_ID_PROP_WHEAT_STRAW, GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
    gpu_draw_sprite(532, 332, SPRITE_ID_PROP_GOLD_CHEST,  GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
}

void app_main(void) {
    printf("========================================================\n");
    printf("   CUSTOM FPGA GPU — 'CATCH THE THIEF' CONSOLE          \n");
    printf("========================================================\n");

    if (gpu_init(GPU_DEFAULT_PIN_SCLK, GPU_DEFAULT_PIN_CS,
                 GPU_DEFAULT_PIN_MOSI, GPU_DEFAULT_PIN_MISO,
                 GPU_DEFAULT_SPI_FREQ_HZ) != 0) {
        printf("[ERROR] Failed to initialize GPU SPI bus!\n");
        return;
    }

    upload_assets_to_fpga();

    int target_npc = 0;
    int zero_x = 248, zero_y = 194;
    bool zero_facing_left = false;
    uint32_t frame_count = 0;
    uint32_t pause_ticks = 0;
    uint8_t clue_mask = 0x1F;

    while (1) {
        draw_village_world(frame_count);

        int16_t dest_x = NPC_CAST[target_npc].talk_x;
        int16_t dest_y = NPC_CAST[target_npc].talk_y;
        int dx = dest_x - zero_x;
        int dy = dest_y - zero_y;
        bool arrived = (abs(dx) <= 4 && abs(dy) <= 4);

        if (arrived) {
            zero_x = dest_x;
            zero_y = dest_y;
            zero_facing_left = NPC_CAST[target_npc].zero_face_left;
            if (++pause_ticks >= 90) {
                pause_ticks = 0;
                target_npc = (target_npc + 1) % AI_NUM_NPCS;
            }
        } else {
            if (abs(dx) > 4) { zero_x += (dx > 0) ? 4 : -4; zero_facing_left = (dx < 0); }
            if (abs(dy) > 4) { zero_y += (dy > 0) ? 4 : -4; }
        }

        for (int i = 0; i < AI_NUM_NPCS; i++) {
            uint16_t spr = ((frame_count >> 4) & 1) ? NPC_CAST[i].spr_action : NPC_CAST[i].spr_idle;
            gpu_draw_sprite(NPC_CAST[i].home_x, NPC_CAST[i].home_y, spr,
                            GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN);
        }

        uint16_t z_spr = arrived ? SPRITE_ID_HERO_ZERO_ACTION :
                         (((frame_count >> 2) & 1) ? SPRITE_ID_HERO_ZERO_WALK1 : SPRITE_ID_HERO_ZERO_WALK2);
        uint8_t z_flags = GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN | (zero_facing_left ? GPU_SPRITE_FLIP_X : 0);
        gpu_draw_sprite(zero_x, zero_y, z_spr, z_flags);

        // Bottom HUD
        gpu_draw_rect(0, 392, 640, 88, COL_HUD_NAVY);
        gpu_draw_line(0, 392, 639, 392, COL_GOLD);
        gpu_draw_sprite(28, 406, SPRITE_ID_HERO_ZERO_PORTRAIT, GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);
        gpu_draw_sprite(80, 406, NPC_CAST[target_npc].spr_portrait, GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);
        for (int h = 0; h < 5; h++) {
            gpu_draw_sprite(126 + h * 20, 418,
                            (h < 4) ? SPRITE_ID_UI_HEART_FULL : SPRITE_ID_UI_HEART_EMPTY,
                            GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
        }
        for (int c = 0; c < 8; c++) {
            if (clue_mask & (1 << c)) {
                gpu_draw_sprite(340 + c * 34, 420, CLUE_PROP_SPRITES[c],
                                GPU_SPRITE_SIZE_16x16 | GPU_SPRITE_TRANS_EN);
            }
        }

        gpu_swap_buffers();
        frame_count++;
        DELAY_MS(16);
    }
}
