/**
 * @file esp32_gpu_demo.ino
 * @brief Arduino Sketch: Custom FPGA GPU 60 FPS Interactive Game Demo
 * @project Custom FPGA-Based GPU — Woxsen University
 * @target ESP32 / ESP32-S3 -> Gowin GW2AR-18C Tang Nano 20K (GPU)
 *
 * Wiring (ESP -> Tang Nano 20K Header):
 *   GND     -> GND    (Common Ground - essential!)
 *   PIN_CS   -> Pin 86 (SPI CS_N)
 *   PIN_SCLK -> Pin 49 (SPI SCLK)
 *   PIN_MOSI -> Pin 48 (SPI MOSI)
 *   PIN_MISO -> Pin 51 (SPI MISO)
 */

#include "gpu_commands.h"
#include "sprites.h"

// =============================================================================
// Pin Configurations
// =============================================================================
// For ESP32-S3:
//   SCLK = GPIO 12, CS = GPIO 10, MOSI = GPIO 11, MISO = GPIO 13
// For Standard Classic ESP32 (WROOM-32 / NodeMCU-32S):
//   Uncomment the lines below:
//   int PIN_SCLK = 18; int PIN_CS = 5; int PIN_MOSI = 23; int PIN_MISO = 19;
int PIN_SCLK = GPU_DEFAULT_PIN_SCLK; // Default ESP32-S3: 12 (or 18 for classic ESP32)
int PIN_CS   = GPU_DEFAULT_PIN_CS;   // Default ESP32-S3: 10 (or 5 for classic ESP32)
int PIN_MOSI = GPU_DEFAULT_PIN_MOSI; // Default ESP32-S3: 11 (or 23 for classic ESP32)
int PIN_MISO = GPU_DEFAULT_PIN_MISO; // Default ESP32-S3: 13 (or 19 for classic ESP32)

#define MAP_COLS 40
#define MAP_ROWS 30

// Game Simulation State
static int player_x = 100;
static int player_y = 200;
static int player_vx = 3;
static int player_vy = 2;
static int player_hp = 100;
static int anim_tick = 0;
static int walk_frame = 0;
static bool facing_left = false;
static uint32_t frame_count = 0;

static int boss_x = 450;
static int boss_y = 120;
static int boss_dir = 1;

static void upload_assets_to_fpga(void) {
    Serial.println("[DEMO] Uploading 256-Color Palette to FPGA CLUT...");
    gpu_load_palette_all(DEFAULT_GPU_PALETTE);

    Serial.println("[DEMO] Uploading Sprite Assets to FPGA SDRAM (Base 0x100000)...");
    for (int i = 0; i < TOTAL_SPRITES_COUNT; i++) {
        const sprite_meta_t *meta = &SPRITE_METADATA[i];
        Serial.printf("  - Uploading %s (ID %u, %ux%u, %u bytes)...\n",
                      meta->name, meta->id, meta->width, meta->height, meta->byte_length);

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
    Serial.println("[DEMO] All sprite assets successfully cached in FPGA SDRAM!");
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

void setup() {
    Serial.begin(115200);
    delay(1500);

    Serial.println("\n========================================================");
    Serial.println("   CUSTOM FPGA GPU — ESP32 INTERACTIVE DEMO             ");
    Serial.println("========================================================");

    // Initialize SPI bus to Tang Nano 20K (4 MHz for reliable sampling on 25.2 MHz FPGA clock)
    int ret = gpu_init(PIN_SCLK, PIN_CS, PIN_MOSI, PIN_MISO, 4000000);
    if (ret != 0) {
        Serial.println("[ERROR] Failed to initialize GPU SPI bus!");
        while (1) delay(1000);
    }

    // Ping GPU
    uint8_t status = gpu_nop();
    Serial.printf("[INIT] GPU Telemetry Status: 0x%02X (Clear=%d, Sprite=%d, Line=%d, Rect=%d, Buffer=%d)\n",
                  status,
                  (status & GPU_STATUS_CLEAR_BUSY) != 0,
                  (status & GPU_STATUS_SPRITE_BUSY) != 0,
                  (status & GPU_STATUS_LINE_BUSY) != 0,
                  (status & GPU_STATUS_RECT_BUSY) != 0,
                  (status & GPU_STATUS_FRONT_BUF) != 0);

    // Upload palette & sprites into FPGA SDRAM/BRAM
    upload_assets_to_fpga();

    Serial.println("\n[DEMO] Starting 60 FPS Render Loop! Check HDMI monitor.\n");
}

void loop() {
    // 1. Clear Active Back Buffer (Deep forest green background: color 2)
    gpu_clear(2);

    // 2. Draw World Background & Structures
    draw_background_scene();

    // 3. Move & Draw 32x32 Boss Monster
    boss_y += boss_dir;
    if (boss_y > 300 || boss_y < 80) boss_dir = -boss_dir;

    gpu_draw_sprite(boss_x, boss_y, SPRITE_ID_BOSS_DRAGON,
                    GPU_SPRITE_SIZE_32x32 | GPU_SPRITE_TRANS_EN);

    // 4. Move & Draw Animated Player Character (16x32)
    player_x += player_x > 500 ? -player_vx : (player_x < 50 ? player_vx : player_vx);
    if (player_x > 500) { player_vx = -3; facing_left = true; }
    if (player_x < 50)  { player_vx = 3;  facing_left = false; }

    anim_tick++;
    if (anim_tick % 10 == 0) {
        walk_frame = 1 - walk_frame;
    }

    uint8_t player_flags = GPU_SPRITE_SIZE_16x32 | GPU_SPRITE_TRANS_EN;
    if (facing_left) {
        player_flags |= GPU_SPRITE_FLIP_X; // Hardware horizontal mirror!
    }

    uint16_t current_sprite_id = (walk_frame == 0) ?
        SPRITE_ID_PLAYER_DOWN_0 : SPRITE_ID_PLAYER_DOWN_1;

    gpu_draw_sprite(player_x, player_y, current_sprite_id, player_flags);

    // 5. Draw UI Overlay (Health Bar, HUD Panels, Crosshair)
    draw_ui_overlay(player_hp, frame_count);

    // 6. Double-Buffer Page Flip
    gpu_swap_buffers();

    frame_count++;
    if (frame_count <= 10 || frame_count % 30 == 0) {
        uint8_t st = gpu_get_status();
        Serial.printf("[RENDER] Frame %lu | Front Buf: %d | GPU Status: 0x%02X (Clear=%d, Sprite=%d, Line=%d, Rect=%d)\n",
                      (unsigned long)frame_count,
                      (st & GPU_STATUS_FRONT_BUF) != 0,
                      st,
                      (st & GPU_STATUS_CLEAR_BUSY) != 0,
                      (st & GPU_STATUS_SPRITE_BUSY) != 0,
                      (st & GPU_STATUS_LINE_BUSY) != 0,
                      (st & GPU_STATUS_RECT_BUSY) != 0);
    }

    delay(1); // Small yield
}
