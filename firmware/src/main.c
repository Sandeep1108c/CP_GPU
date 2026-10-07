/**
 * @file main.c
 * @brief Custom FPGA-Based GPU 60 FPS Interactive Game Demo
 * @project Custom FPGA-Based GPU — Woxsen University
 * @target ESP32-S3 -> Gowin GW2AR-18C Tang Nano 20K
 *
 * Demonstrates the full capabilities of the custom GPU:
 * 1. High-speed SPI link initialization (20 MHz)
 * 2. Uploading 256-color palette to FPGA BRAM CLUT
 * 3. Streaming 2D sprite sheets into FPGA SDRAM asset bank (0x100000+)
 * 4. Hardware-accelerated tilemap background rendering
 * 5. Animated 16x32 player character walking with transparency & horizontal flip
 * 6. 32x32 boss monster blitting
 * 7. Hardware geometric primitives (UI dialog box, health bar, radar crosshair)
 * 8. Tear-free 60 FPS double-buffering page flip on VSYNC
 */

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "gpu_commands.h"
#include "sprites.h"

#if defined(ESP_PLATFORM)
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
static const char *TAG = "GPU_DEMO";
#define DELAY_MS(ms) vTaskDelay(pdMS_TO_TICKS(ms))
#else
#define DELAY_MS(ms)
#endif

// World tilemap grid dimensions (40x30 tiles of 16x16 = 640x480 screen)
#define MAP_COLS 40
#define MAP_ROWS 30

static void upload_assets_to_fpga(void) {
    printf("[DEMO] Uploading 256-Color Palette to FPGA CLUT...\n");
    gpu_load_palette_all(DEFAULT_GPU_PALETTE);

    printf("[DEMO] Uploading Sprite Assets to FPGA SDRAM (Base 0x100000)...\n");
    for (int i = 0; i < TOTAL_SPRITES_COUNT; i++) {
        const sprite_meta_t *meta = &SPRITE_METADATA[i];
        printf("  - Uploading %s (ID %u, %ux%u, %u bytes) to SDRAM offset 0x%06lX...\n",
               meta->name, meta->id, meta->width, meta->height, meta->byte_length,
               (unsigned long)(0x100000 + meta->sdram_offset));

        // Point to sprite byte data
        const uint8_t *data_ptr = NULL;
        switch (meta->id) {
            case SPRITE_ID_TILE_GRASS:    data_ptr = SPRITE_DATA_TILE_GRASS; break;
            case SPRITE_ID_TILE_STONE:    data_ptr = SPRITE_DATA_TILE_STONE; break;
            case SPRITE_ID_TILE_WATER:    data_ptr = SPRITE_DATA_TILE_WATER; break;
            case SPRITE_ID_TILE_WALL:     data_ptr = SPRITE_DATA_TILE_WALL; break;
            case SPRITE_ID_PLAYER_DOWN_0: data_ptr = SPRITE_DATA_PLAYER_DOWN_0; break;
            case SPRITE_ID_PLAYER_DOWN_1: data_ptr = SPRITE_DATA_PLAYER_DOWN_1; break;
            case SPRITE_ID_BOSS_DRAGON:   data_ptr = SPRITE_DATA_BOSS_DRAGON; break;
            default: break;
        }

        if (data_ptr) {
            gpu_load_sprite_data(0x100000 + meta->sdram_offset, data_ptr, meta->byte_length);
        }
    }
    printf("[DEMO] All assets successfully cached in FPGA SDRAM!\n");
}

static void draw_background_scene(void) {
    // 1. Draw top & bottom stone pathways
    for (int col = 0; col < MAP_COLS; col++) {
        gpu_draw_sprite(col * 16, 0, SPRITE_ID_TILE_WALL, GPU_SPRITE_SIZE_16x16);
        gpu_draw_sprite(col * 16, 480 - 16, SPRITE_ID_TILE_WALL, GPU_SPRITE_SIZE_16x16);
    }

    // 2. Draw vertical wall borders
    for (int row = 1; row < MAP_ROWS - 1; row++) {
        gpu_draw_sprite(0, row * 16, SPRITE_ID_TILE_WALL, GPU_SPRITE_SIZE_16x16);
        gpu_draw_sprite(640 - 16, row * 16, SPRITE_ID_TILE_WALL, GPU_SPRITE_SIZE_16x16);
    }

    // 3. Central stone pathway
    for (int col = 5; col < 35; col++) {
        gpu_draw_sprite(col * 16, 240 - 8, SPRITE_ID_TILE_STONE, GPU_SPRITE_SIZE_16x16);
    }

    // 4. Water pond (4x3 tiles at bottom-left)
    for (int r = 0; r < 3; r++) {
        for (int c = 0; c < 4; c++) {
            gpu_draw_sprite((3 + c) * 16, (18 + r) * 16, SPRITE_ID_TILE_WATER, GPU_SPRITE_SIZE_16x16);
        }
    }
}

static void draw_ui_overlay(int player_hp, int score) {
    // 1. Top HUD Bar Background (dark slate rectangle)
    gpu_draw_rect(20, 20, 260, 48, 8); // Color 8 = Dark Gray

    // 2. White Border around HUD
    gpu_draw_line(20, 20, 280, 20, 15);
    gpu_draw_line(280, 20, 280, 68, 15);
    gpu_draw_line(280, 68, 20, 68, 15);
    gpu_draw_line(20, 68, 20, 20, 15);

    // 3. Health Bar (Red background + Green current HP)
    gpu_draw_rect(30, 32, 200, 14, 4); // Red
    int green_w = (player_hp * 200) / 100;
    if (green_w > 0) {
        gpu_draw_rect(30, 32, green_w, 14, 10); // Bright Green
    }

    // 4. Radar Crosshair (top-right corner)
    gpu_draw_line(600, 30, 600, 70, 11); // Bright Cyan
    gpu_draw_line(580, 50, 620, 50, 11);
}

void app_main(void) {
    printf("========================================================\n");
    printf("   CUSTOM FPGA GPU — ESP32-S3 DEMO APPLICATION          \n");
    printf("========================================================\n");

    // Initialize SPI connection to Tang Nano 20K
    int ret = gpu_init(GPU_DEFAULT_PIN_SCLK,
                       GPU_DEFAULT_PIN_CS,
                       GPU_DEFAULT_PIN_MOSI,
                       GPU_DEFAULT_PIN_MISO,
                       GPU_DEFAULT_SPI_FREQ_HZ);
    if (ret != 0) {
        printf("[ERROR] Failed to initialize GPU SPI bus!\n");
        return;
    }

    // Ping GPU
    uint8_t status = gpu_nop();
    printf("[INIT] GPU Telemetry Status: 0x%02X (Busy=%d, VBLANK=%d, Buffer=%d, Error=%d)\n",
           status,
           (status & GPU_STATUS_BUSY) != 0,
           (status & GPU_STATUS_IN_VBLANK) != 0,
           (status & GPU_STATUS_FRONT_BUF) != 0,
           (status & GPU_STATUS_ERROR) != 0);

    // Upload palette & sprites to FPGA memory
    upload_assets_to_fpga();

    // Game Simulation State Variables
    int player_x = 100;
    int player_y = 200;
    int player_vx = 3;
    int player_vy = 2;
    int player_hp = 100;
    int anim_tick = 0;
    int walk_frame = 0;
    bool facing_left = false;
    uint32_t frame_count = 0;

    int boss_x = 450;
    int boss_y = 120;
    int boss_dir = 1;

    printf("\n[DEMO] Starting 60 FPS Render Loop! Enjoy the show on your HDMI monitor!\n");

    while (1) {
        // -------------------------------------------------------------
        // 1. Clear Active Back Buffer (Deep forest green background: color 2)
        // -------------------------------------------------------------
        gpu_clear(2);

        // -------------------------------------------------------------
        // 2. Draw World Background & Structures
        // -------------------------------------------------------------
        draw_background_scene();

        // -------------------------------------------------------------
        // 3. Move & Draw 32x32 Boss Monster
        // -------------------------------------------------------------
        boss_y += boss_dir;
        if (boss_y > 300 || boss_y < 80) boss_dir = -boss_dir;

        // Render Boss with Transparency enabled
        gpu_draw_sprite(boss_x, boss_y, SPRITE_ID_BOSS_DRAGON,
                        GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);

        // -------------------------------------------------------------
        // 4. Move & Draw Animated Player Character (16x32)
        // -------------------------------------------------------------
        player_x += player_x > 500 ? -player_vx : (player_x < 50 ? player_vx : player_vx);
        if (player_x > 500) { player_vx = -3; facing_left = true; }
        if (player_x < 50)  { player_vx = 3;  facing_left = false; }

        anim_tick++;
        if (anim_tick % 10 == 0) {
            walk_frame = 1 - walk_frame;
        }

        uint8_t player_flags = GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN;
        if (facing_left) {
            player_flags |= GPU_SPRITE_FLIP_X; // Hardware horizontal flip!
        }

        uint16_t current_sprite_id = (walk_frame == 0) ?
            SPRITE_ID_PLAYER_DOWN_0 : SPRITE_ID_PLAYER_DOWN_1;

        gpu_draw_sprite(player_x, player_y, current_sprite_id, player_flags);

        // -------------------------------------------------------------
        // 5. Draw UI Overlay (Health Bar, HUD Panels, Crosshair)
        // -------------------------------------------------------------
        draw_ui_overlay(player_hp, frame_count);

        // -------------------------------------------------------------
        // 6. Double-Buffer Page Flip Synchronized to VSYNC
        // -------------------------------------------------------------
        gpu_swap_buffers();

        // Wait for VSYNC
        gpu_wait_vblank();

        frame_count++;
        if (frame_count % 60 == 0) {
            // Log telemetry every 1 second (60 frames)
            uint8_t st = gpu_get_status();
            printf("[FPS 60] Rendered %lu frames | Front Buf: %d | GPU Status: 0x%02X\n",
                   (unsigned long)frame_count, (st & GPU_STATUS_FRONT_BUF) != 0, st);
        }

        DELAY_MS(16); // ~60 Hz frame pacing
    }
}
