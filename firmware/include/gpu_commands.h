/**
 * @file gpu_commands.h
 * @brief Custom FPGA-Based GPU Driver & Command Protocol Header
 * @project Custom FPGA-Based GPU — Woxsen University
 * @target ESP32-S3 (SPI Master) -> Gowin GW2AR-18C Tang Nano 20K (GPU Slave)
 *
 * Provides high-level hardware-accelerated 2D graphics APIs:
 * - Double-buffered tear-free rendering (640x480 @ 60 Hz)
 * - Bresenham line drawing
 * - Solid rectangle fills
 * - 2D sprite blitting (16x16, 16x32, 32x32, 64x64, 8x8)
 * - Color-key transparency and dual-axis mirroring
 * - 256-color palette (CLUT) programming
 * - Direct SDRAM asset streaming
 */

#ifndef GPU_COMMANDS_H
#define GPU_COMMANDS_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// GPU Command Opcodes
// =============================================================================
#define GPU_OP_NOP          0x00  /**< No operation; clears error flags and returns telemetry */
#define GPU_OP_CLEAR        0x01  /**< Wipe entire active back buffer with 8-bit palette color */
#define GPU_OP_DRAW_SPRITE  0x02  /**< Blit sprite from SDRAM asset memory into active back buffer */
#define GPU_OP_DRAW_LINE    0x03  /**< Hardware Bresenham line drawing */
#define GPU_OP_DRAW_RECT    0x04  /**< Hardware solid filled rectangle */
#define GPU_OP_SET_PALETTE  0x05  /**< Program 24-bit TrueColor entry into Color Lookup Table */
#define GPU_OP_SWAP_BUFFER  0x06  /**< Request tear-free double buffer flip synchronized to VSYNC */
#define GPU_OP_LOAD_SPRITE  0x07  /**< Stream raw 8-bit pixel assets directly into FPGA SDRAM */

// =============================================================================
// Sprite Transformation & Size Flags (flags argument in gpu_draw_sprite)
// =============================================================================
#define GPU_SPRITE_FLIP_X        (1 << 0)  /**< Horizontal mirror (invert columns) */
#define GPU_SPRITE_FLIP_Y        (1 << 1)  /**< Vertical mirror (invert rows) */
#define GPU_SPRITE_TRANS_EN      (1 << 2)  /**< Skip index 0x00 (transparent background) */

// Size mode presets (bits 5:3)
#define GPU_SPRITE_SIZE_16x16    (0 << 3)  /**< 16x16 standard world/tile sprites (256 bytes) */
#define GPU_SPRITE_SIZE_16x32    (1 << 3)  /**< 16x32 player/character/NPC sprites (512 bytes) */
#define GPU_SPRITE_SIZE_32x32    (2 << 3)  /**< 32x32 boss/large monster sprites (1024 bytes) */
#define GPU_SPRITE_SIZE_64x64    (3 << 3)  /**< 64x64 dialogue avatar/portrait (4096 bytes) */
#define GPU_SPRITE_SIZE_8x8      (4 << 3)  /**< 8x8 font glyph / UI icons (64 bytes) */

// =============================================================================
// Telemetry Status Byte Bitmask (returned via MISO)
// =============================================================================
#define GPU_STATUS_CLEAR_BUSY    (1 << 0)  /**< 1 while clear engine is running */
#define GPU_STATUS_SPRITE_BUSY   (1 << 1)  /**< 1 while sprite blitter is running */
#define GPU_STATUS_LINE_BUSY     (1 << 2)  /**< 1 while line rasterizer is running */
#define GPU_STATUS_RECT_BUSY     (1 << 3)  /**< 1 while rect rasterizer is running */
#define GPU_STATUS_FRONT_BUF     (1 << 4)  /**< Currently scanned-out front buffer (0 or 1) */
#define GPU_STATUS_BUSY          (GPU_STATUS_CLEAR_BUSY | GPU_STATUS_SPRITE_BUSY | GPU_STATUS_LINE_BUSY | GPU_STATUS_RECT_BUSY)
#define GPU_STATUS_SIG_MASK      0xE0      /**< Bits 7:5 must match signature 3'b010 (0x40) */
#define GPU_STATUS_SIG_EXPECTED  0x40

// =============================================================================
// Standard Hardware Pin Defaults (Tang Nano 20K <-> ESP32-S3)
// =============================================================================
#define GPU_DEFAULT_PIN_SCLK     12   /**< Connects to Tang Nano 20K Pin 49 (SCLK) */
#define GPU_DEFAULT_PIN_CS       10   /**< Connects to Tang Nano 20K Pin 86 (CS_N) */
#define GPU_DEFAULT_PIN_MOSI     11   /**< Connects to Tang Nano 20K Pin 48 (MOSI) */
#define GPU_DEFAULT_PIN_MISO     13   /**< Connects to Tang Nano 20K Pin 51 (MISO) */
#define GPU_DEFAULT_SPI_FREQ_HZ  20000000  /**< 20 MHz default SPI clock rate */

// =============================================================================
// Driver Initialization & Control Functions
// =============================================================================

/**
 * @brief Initialize the high-speed SPI master bus and GPU communication link.
 * @param sclk_pin GPIO pin for SPI Clock
 * @param cs_pin   GPIO pin for active-low Chip Select
 * @param mosi_pin GPIO pin for Master-Out-Slave-In
 * @param miso_pin GPIO pin for Master-In-Slave-Out
 * @param freq_hz  Clock frequency in Hz (typically 10_000_000 to 30_000_000)
 * @return 0 on success, negative on failure.
 */
int gpu_init(int sclk_pin, int cs_pin, int mosi_pin, int miso_pin, uint32_t freq_hz);

/**
 * @brief Ping the GPU with NOP, retrieve hardware telemetry, and clear error flags.
 * @return 8-bit telemetry status byte.
 */
uint8_t gpu_nop(void);

/**
 * @brief Query current GPU telemetry without sending a heavy payload.
 * @return 8-bit telemetry byte.
 */
uint8_t gpu_get_status(void);

/**
 * @brief Block CPU execution until the GPU has finished all active rendering commands.
 */
void gpu_wait_idle(void);

/**
 * @brief Block CPU execution until the GPU enters vertical blanking (VSYNC interval).
 */
void gpu_wait_vblank(void);

// =============================================================================
// Hardware-Accelerated 2D Drawing Primitives
// =============================================================================

/**
 * @brief Wipe the active back buffer with a solid palette color.
 * @param color 8-bit palette index (0..255)
 */
void gpu_clear(uint8_t color);

/**
 * @brief Draw a 2D line using the FPGA's hardware Bresenham line engine.
 * @param x0    Start X coordinate (-32768 to 32767)
 * @param y0    Start Y coordinate (-32768 to 32767)
 * @param x1    End X coordinate (-32768 to 32767)
 * @param y1    End Y coordinate (-32768 to 32767)
 * @param color 8-bit palette color index
 */
void gpu_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint8_t color);

/**
 * @brief Fill a solid rectangle in the active back buffer.
 * @param x     Top-left X coordinate (-32768 to 32767)
 * @param y     Top-left Y coordinate (-32768 to 32767)
 * @param w     Width in pixels (0 to 65535)
 * @param h     Height in pixels (0 to 65535)
 * @param color 8-bit palette color index
 */
void gpu_draw_rect(int16_t x, int16_t y, uint16_t w, uint16_t h, uint8_t color);

/**
 * @brief Blit a 2D sprite from FPGA SDRAM memory into the active back buffer.
 * @param x         Screen destination X (-32768 to 32767)
 * @param y         Screen destination Y (-32768 to 32767)
 * @param sprite_id Asset bank sprite index (0..65535)
 * @param flags     Bitmask of GPU_SPRITE_FLIP_X, GPU_SPRITE_FLIP_Y, GPU_SPRITE_TRANS_EN,
 *                  and size mode (e.g. GPU_SPRITE_SIZE_16x32)
 */
void gpu_draw_sprite(int16_t x, int16_t y, uint16_t sprite_id, uint8_t flags);

// =============================================================================
// Color Palette & Frame Synchronization
// =============================================================================

/**
 * @brief Program a 24-bit TrueColor RGB entry in the FPGA's Color Lookup Table.
 * @param index Palette index (0..255)
 * @param r     Red channel (0..255)
 * @param g     Green channel (0..255)
 * @param b     Blue channel (0..255)
 */
void gpu_set_palette(uint8_t index, uint8_t r, uint8_t g, uint8_t b);

/**
 * @brief Load an entire 256-color palette (768 bytes: R, G, B triplets).
 * @param palette_rgb_array Array of 768 bytes.
 */
void gpu_load_palette_all(const uint8_t palette_rgb_array[768]);

/**
 * @brief Request an atomic double-buffer page flip.
 *        The FPGA will swap front and back buffers at the very next VSYNC rising edge.
 */
void gpu_swap_buffers(void);

// =============================================================================
// Asset Streaming
// =============================================================================

/**
 * @brief Stream raw sprite pixel bytes into the FPGA's SDRAM asset storage bank.
 * @param sdram_byte_addr 24-bit destination address (e.g. 0x100000 + offset)
 * @param data            Pointer to pixel data buffer
 * @param length          Number of bytes to write
 */
void gpu_load_sprite_data(uint32_t sdram_byte_addr, const uint8_t *data, uint16_t length);

#ifdef __cplusplus
}
#endif

#endif // GPU_COMMANDS_H
