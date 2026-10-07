/**
 * @file gpu_commands.c
 * @brief Custom FPGA-Based GPU Driver & Command Protocol Implementation
 * @project Custom FPGA-Based GPU — Woxsen University
 * @target ESP32-S3 (SPI Master) -> Gowin GW2AR-18C Tang Nano 20K (GPU Slave)
 */

#include "gpu_commands.h"
#include <string.h>

#if defined(ESP_PLATFORM)
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "rom/ets_sys.h"

static const char *TAG = "GPU_DRIVER";
static spi_device_handle_t s_spi_dev = NULL;
static int s_cs_pin = -1;

#elif defined(ARDUINO)
#include <SPI.h>
static int s_cs_pin = -1;
static SPISettings s_spi_settings(20000000, MSBFIRST, SPI_MODE0);

#else
// Standalone / Mock desktop simulation mode
#include <stdio.h>
static int s_cs_pin = -1;
#endif

// =============================================================================
// Low-Level SPI Packet Transmission
// =============================================================================

static inline void cs_low(void) {
#if defined(ESP_PLATFORM)
    gpio_set_level((gpio_num_t)s_cs_pin, 0);
#elif defined(ARDUINO)
    digitalWrite(s_cs_pin, LOW);
#endif
}

static inline void cs_high(void) {
#if defined(ESP_PLATFORM)
    gpio_set_level((gpio_num_t)s_cs_pin, 1);
#elif defined(ARDUINO)
    digitalWrite(s_cs_pin, HIGH);
#endif
}

void gpu_wait_idle(void);

/**
 * @brief Transmit a raw packet: [CMD (8b)] [LEN (8b)] [PAYLOAD (N bytes)]
 *        Simultaneously captures telemetry returned on MISO.
 */
static uint8_t spi_transfer_packet(uint8_t cmd, uint8_t len, const uint8_t *payload, uint8_t *rx_buf) {
    uint8_t tx_header[2] = {cmd, len};
    uint8_t last_telemetry = 0x00;

#if defined(ESP_PLATFORM)
    if (!s_spi_dev) return 0xFF;

    cs_low();

    // 1. Send Header [CMD, LEN] and capture telemetry
    uint8_t rx_header[2] = {0, 0};
    spi_transaction_t t_hdr;
    memset(&t_hdr, 0, sizeof(t_hdr));
    t_hdr.length = 16;
    t_hdr.tx_buffer = tx_header;
    t_hdr.rx_buffer = rx_header;
    spi_device_polling_transmit(s_spi_dev, &t_hdr);
    last_telemetry = rx_header[0];

    // 2. Send Payload (if any)
    if (len > 0 && payload != NULL) {
        spi_transaction_t t_data;
        memset(&t_data, 0, sizeof(t_data));
        t_data.length = len * 8;
        t_data.tx_buffer = payload;
        t_data.rx_buffer = rx_buf;
        spi_device_polling_transmit(s_spi_dev, &t_data);
    }

    cs_high();

#elif defined(ARDUINO)
    SPI.beginTransaction(s_spi_settings);
    cs_low();

    last_telemetry = SPI.transfer(tx_header[0]);
    SPI.transfer(tx_header[1]);

    for (int i = 0; i < len; i++) {
        uint8_t b = SPI.transfer(payload ? payload[i] : 0x00);
        if (rx_buf) rx_buf[i] = b;
    }

    cs_high();
    SPI.endTransaction();

#else
    // Desktop Mock / Simulation Trace
    last_telemetry = GPU_STATUS_SIG_EXPECTED; // simulated idle
#endif

    return last_telemetry;
}

// =============================================================================
// Driver Initialization & Control Functions
// =============================================================================

int gpu_init(int sclk_pin, int cs_pin, int mosi_pin, int miso_pin, uint32_t freq_hz) {
    s_cs_pin = cs_pin;

#if defined(ESP_PLATFORM)
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << s_cs_pin),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    cs_high();

    spi_bus_config_t buscfg = {
        .mosi_io_num = mosi_pin,
        .miso_io_num = miso_pin,
        .sclk_io_num = sclk_pin,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4096
    };

    esp_err_t ret = spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize SPI bus: %d", ret);
        return -1;
    }

    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = (int)freq_hz,
        .mode = 0, // SPI Mode 0 (CPOL=0, CPHA=0)
        .spics_io_num = -1, // Manual CS control
        .queue_size = 7
    };

    ret = spi_bus_add_device(SPI2_HOST, &devcfg, &s_spi_dev);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to add SPI device: %d", ret);
        return -1;
    }

    ESP_LOGI(TAG, "GPU SPI Master initialized at %lu MHz", freq_hz / 1000000);

#elif defined(ARDUINO)
    pinMode(s_cs_pin, OUTPUT);
    cs_high();
    SPI.begin(sclk_pin, miso_pin, mosi_pin, s_cs_pin);
    s_spi_settings = SPISettings(freq_hz, MSBFIRST, SPI_MODE0);
#endif

    // Send NOP to clear any power-on error and read telemetry
    uint8_t status = gpu_nop();
    return 0;
}

uint8_t gpu_nop(void) {
    return spi_transfer_packet(GPU_OP_NOP, 0, NULL, NULL);
}

uint8_t gpu_get_status(void) {
    return gpu_nop();
}

void gpu_wait_idle(void) {
    // One in-flight draw command is supported by the FPGA executor.  A clear
    // can span many frames while scanout shares SDRAM, so do not use a fixed
    // 16 ms completion delay.
#if defined(ESP_PLATFORM)
    ets_delay_us(10);
#elif defined(ARDUINO)
    delayMicroseconds(10);
#endif
    uint32_t count = 250000; // 500 ms at the 2 us polling interval
    while ((gpu_get_status() & GPU_STATUS_BUSY) && --count) {
#if defined(ESP_PLATFORM)
        ets_delay_us(2);
#elif defined(ARDUINO)
        delayMicroseconds(2);
#endif
    }
}

void gpu_wait_vblank(void) {
    gpu_wait_idle();
}

// =============================================================================
// Hardware-Accelerated 2D Drawing Primitives
// =============================================================================

void gpu_clear(uint8_t color) {
    uint8_t payload[1] = {color};
    spi_transfer_packet(GPU_OP_CLEAR, 1, payload, NULL);
    gpu_wait_idle();
}

void gpu_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint8_t color) {
    uint8_t payload[9];
    // Big-endian 16-bit encoding
    payload[0] = (uint8_t)((x0 >> 8) & 0xFF);
    payload[1] = (uint8_t)(x0 & 0xFF);
    payload[2] = (uint8_t)((y0 >> 8) & 0xFF);
    payload[3] = (uint8_t)(y0 & 0xFF);
    payload[4] = (uint8_t)((x1 >> 8) & 0xFF);
    payload[5] = (uint8_t)(x1 & 0xFF);
    payload[6] = (uint8_t)((y1 >> 8) & 0xFF);
    payload[7] = (uint8_t)(y1 & 0xFF);
    payload[8] = color;

    spi_transfer_packet(GPU_OP_DRAW_LINE, 9, payload, NULL);
    gpu_wait_idle();
}

void gpu_draw_rect(int16_t x, int16_t y, uint16_t w, uint16_t h, uint8_t color) {
    uint8_t payload[9];
    payload[0] = (uint8_t)((x >> 8) & 0xFF);
    payload[1] = (uint8_t)(x & 0xFF);
    payload[2] = (uint8_t)((y >> 8) & 0xFF);
    payload[3] = (uint8_t)(y & 0xFF);
    payload[4] = (uint8_t)((w >> 8) & 0xFF);
    payload[5] = (uint8_t)(w & 0xFF);
    payload[6] = (uint8_t)((h >> 8) & 0xFF);
    payload[7] = (uint8_t)(h & 0xFF);
    payload[8] = color;

    spi_transfer_packet(GPU_OP_DRAW_RECT, 9, payload, NULL);
    gpu_wait_idle();
}

void gpu_draw_sprite(int16_t x, int16_t y, uint16_t sprite_id, uint8_t flags) {
    uint8_t payload[7];
    payload[0] = (uint8_t)((x >> 8) & 0xFF);
    payload[1] = (uint8_t)(x & 0xFF);
    payload[2] = (uint8_t)((y >> 8) & 0xFF);
    payload[3] = (uint8_t)(y & 0xFF);
    payload[4] = (uint8_t)((sprite_id >> 8) & 0xFF);
    payload[5] = (uint8_t)(sprite_id & 0xFF);
    payload[6] = flags;

    spi_transfer_packet(GPU_OP_DRAW_SPRITE, 7, payload, NULL);
    gpu_wait_idle();
}

// =============================================================================
// Color Palette & Frame Synchronization
// =============================================================================

void gpu_set_palette(uint8_t index, uint8_t r, uint8_t g, uint8_t b) {
    uint8_t payload[4] = {index, r, g, b};
    spi_transfer_packet(GPU_OP_SET_PALETTE, 4, payload, NULL);
}

void gpu_load_palette_all(const uint8_t palette_rgb_array[768]) {
    for (int i = 0; i < 256; i++) {
        gpu_set_palette((uint8_t)i,
                        palette_rgb_array[i * 3 + 0],
                        palette_rgb_array[i * 3 + 1],
                        palette_rgb_array[i * 3 + 2]);
    }
}

void gpu_swap_buffers(void) {
    gpu_wait_idle();
    spi_transfer_packet(GPU_OP_SWAP_BUFFER, 0, NULL, NULL);
}

// =============================================================================
// Asset Streaming
// =============================================================================

void gpu_load_sprite_data(uint32_t sdram_byte_addr, const uint8_t *data, uint16_t length) {
    // Break large uploads into chunks of up to 252 bytes (packet limit)
    uint16_t offset = 0;
    while (offset < length) {
        uint8_t chunk = (length - offset > 252) ? 252 : (uint8_t)(length - offset);
        uint8_t packet[256];
        uint32_t curr_addr = sdram_byte_addr + offset;

        // 3-byte SDRAM Address (24-bit big endian)
        packet[0] = (uint8_t)((curr_addr >> 16) & 0xFF);
        packet[1] = (uint8_t)((curr_addr >> 8) & 0xFF);
        packet[2] = (uint8_t)(curr_addr & 0xFF);

        // Copy chunk data
        memcpy(&packet[3], &data[offset], chunk);

        spi_transfer_packet(GPU_OP_LOAD_SPRITE, chunk + 3, packet, NULL);
        gpu_wait_idle();

        offset += chunk;
    }
}
