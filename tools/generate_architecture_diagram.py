#!/usr/bin/env python3
"""
Generate High-Resolution System Architecture Diagrams for Final Presentation & Defense Report.
Custom FPGA GPU & Edge AI Project — Woxsen University

Generates:
  1. docs/system_architecture_diagram.png (High-Resolution Light Theme for .docx / .odt reports)
  2. docs/system_architecture_diagram_dark.png (High-Resolution Dark Theme for Presentation Slides)
"""

import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)


def draw_arrow(draw, start, end, color=(71, 85, 105), width=3, arrow_size=8, vertical=True):
    """Draws a line with an arrowhead at the end."""
    draw.line([start, end], fill=color, width=width)
    x2, y2 = end
    if vertical:
        # pointing down
        if end[1] > start[1]:
            pts = [(x2, y2), (x2 - arrow_size, y2 - arrow_size * 1.5), (x2 + arrow_size, y2 - arrow_size * 1.5)]
        else:
            pts = [(x2, y2), (x2 - arrow_size, y2 + arrow_size * 1.5), (x2 + arrow_size, y2 + arrow_size * 1.5)]
    else:
        # horizontal pointing right
        if end[0] > start[0]:
            pts = [(x2, y2), (x2 - arrow_size * 1.5, y2 - arrow_size), (x2 - arrow_size * 1.5, y2 + arrow_size)]
        else:
            pts = [(x2, y2), (x2 + arrow_size * 1.5, y2 - arrow_size), (x2 + arrow_size * 1.5, y2 + arrow_size)]
    draw.polygon(pts, fill=color)


def create_diagram(theme="light"):
    # High-resolution 2200 x 1280 canvas
    w, h = 2200, 1280

    if theme == "light":
        bg_color = (248, 250, 252) # Slate 50
        text_primary = (15, 23, 42) # Slate 900
        text_muted = (71, 85, 105) # Slate 600
        card_bg = (255, 255, 255)
        card_border = (203, 213, 225) # Slate 300
        esp_banner = (30, 58, 138) # Blue 900
        fpga_banner = (15, 118, 110) # Teal 700
        subcard_bg = (241, 245, 249) # Slate 100
        subcard_border = (226, 232, 240)
        wire_color = (100, 116, 139) # Slate 500
        accent_blue = (2, 132, 199)
        accent_green = (16, 185, 129)
        accent_amber = (217, 119, 6)
        accent_purple = (124, 58, 237)
        badge_bg = (224, 231, 255)
        badge_text = (30, 58, 138)
    else:
        bg_color = (11, 15, 25) # Deep Dark
        text_primary = (241, 245, 249)
        text_muted = (148, 163, 184)
        card_bg = (19, 26, 42)
        card_border = (45, 55, 75)
        esp_banner = (30, 64, 175)
        fpga_banner = (13, 148, 136)
        subcard_bg = (26, 36, 56)
        subcard_border = (51, 65, 85)
        wire_color = (148, 163, 184)
        accent_blue = (56, 189, 248)
        accent_green = (52, 211, 153)
        accent_amber = (245, 158, 11)
        accent_purple = (167, 139, 250)
        badge_bg = (30, 41, 59)
        badge_text = (191, 219, 254)

    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        f_super = ImageFont.truetype("segoeuib.ttf", 32)
        f_title = ImageFont.truetype("segoeuib.ttf", 24)
        f_subtitle = ImageFont.truetype("segoeui.ttf", 15)
        f_card_hdr = ImageFont.truetype("segoeuib.ttf", 18)
        f_card_sub = ImageFont.truetype("segoeuib.ttf", 14)
        f_body_bold = ImageFont.truetype("segoeuib.ttf", 13)
        f_body = ImageFont.truetype("segoeui.ttf", 12)
        f_small = ImageFont.truetype("segoeui.ttf", 11)
        f_mono = ImageFont.truetype("consola.ttf", 12)
        f_mono_bold = ImageFont.truetype("consolab.ttf", 13)
    except:
        f_super = ImageFont.load_default()
        f_title = f_super
        f_subtitle = f_super
        f_card_hdr = f_super
        f_card_sub = f_super
        f_body_bold = f_super
        f_body = f_super
        f_small = f_super
        f_mono = f_super
        f_mono_bold = f_super

    # 1. Top Header Banner
    header_y = 70
    draw.text((60, 25), "WOXSEN UNIVERSITY — SCHOOL OF TECHNOLOGY | CAPSTONE ENGINEERING DEFENSE", font=f_subtitle, fill=text_muted)
    draw.text((60, 48), "High-Level System Hardware & Software Architecture Diagram", font=f_super, fill=text_primary)

    # Metadata pill
    meta_text = "Sipeed Tang Nano 20K (Gowin GW2AR-18C)  |  ESP32-S3 Dual-Core Host  |  DVI/HDMI 640x480 @ 60 FPS"
    draw.rounded_rectangle([1320, 35, 2140, 75], radius=6, fill=badge_bg, outline=card_border, width=1)
    draw.text((1340, 47), meta_text, font=f_body_bold, fill=badge_text)

    draw.line([(60, header_y + 20), (2140, header_y + 20)], fill=card_border, width=1)

    # -------------------------------------------------------------------------
    # LEFT CONTAINER: ESP32-S3 HOST CONTROLLER
    # -------------------------------------------------------------------------
    esp_x1, esp_y1, esp_x2, esp_y2 = 60, 110, 720, 1160
    draw.rounded_rectangle([esp_x1, esp_y1, esp_x2, esp_y2], radius=12, fill=card_bg, outline=card_border, width=2)

    # ESP Header Bar
    draw.rounded_rectangle([esp_x1, esp_y1, esp_x2, esp_y1 + 55], radius=12, fill=esp_banner)
    draw.rectangle([esp_x1, esp_y1 + 40, esp_x2, esp_y1 + 55], fill=esp_banner) # square bottom corners
    draw.text((esp_x1 + 20, esp_y1 + 12), "ESP32-S3 HOST CONTROLLER", font=f_title, fill=(255, 255, 255))
    draw.text((esp_x1 + 420, esp_y1 + 18), "240 MHz Dual-Core LX7", font=f_subtitle, fill=(219, 234, 254))

    # --- ESP Subcard 1: nanoGPT Edge AI Engine ---
    ai_x1, ai_y1, ai_x2, ai_y2 = esp_x1 + 20, esp_y1 + 75, esp_x2 - 20, esp_y1 + 355
    draw.rounded_rectangle([ai_x1, ai_y1, ai_x2, ai_y2], radius=8, fill=subcard_bg, outline=subcard_border, width=1)
    draw.rounded_rectangle([ai_x1, ai_y1, ai_x2, ai_y1 + 32], radius=8, fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.rectangle([ai_x1, ai_y1 + 20, ai_x2, ai_y1 + 32], fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.text((ai_x1 + 12, ai_y1 + 7), "🧠  nanoGPT Edge AI Engine (NLP & Persona)", font=f_card_hdr, fill=(255, 255, 255))

    ai_bullets = [
        ("Architecture:", "4.79 Million Parameters (6 Layers, 6 Heads, 384 Embedding Dim)"),
        ("Quantization:", "INT8 Weight Quantized (4.78 MB Total Memory Footprint)"),
        ("Conditioning:", "<|culprit|> <|npc|> <|trust|> <|memory|> <|mood|> Structured Prompts"),
        ("Mystery Logic:", "4 Alternate Culprits (Shopkeeper, Farmer, Guard, Old Man)"),
        ("Intent Engine:", "Stateful Multi-Tier Dialogue Matcher (Tiers 1 -> 2 -> 3 Clues)"),
        ("Performance:", "~180 ms Latency per Interrogation Turn (0 Token Glitches)"),
    ]
    cur_y = ai_y1 + 42
    for b_title, b_desc in ai_bullets:
        draw.text((ai_x1 + 15, cur_y), b_title, font=f_body_bold, fill=accent_blue)
        draw.text((ai_x1 + 120, cur_y), b_desc, font=f_body, fill=text_primary)
        cur_y += 24

    # Arrow AI -> Game Engine
    draw_arrow(draw, (esp_x1 + (esp_x2 - esp_x1)//2, ai_y2), (esp_x1 + (esp_x2 - esp_x1)//2, ai_y2 + 25), color=wire_color)

    # --- ESP Subcard 2: Game Engine & Graphics Driver ---
    ge_y1 = ai_y2 + 25
    ge_y2 = ge_y1 + 340
    draw.rounded_rectangle([ai_x1, ge_y1, ai_x2, ge_y2], radius=8, fill=subcard_bg, outline=subcard_border, width=1)
    draw.rounded_rectangle([ai_x1, ge_y1, ai_x2, ge_y1 + 32], radius=8, fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.rectangle([ai_x1, ge_y1 + 20, ai_x2, ge_y1 + 32], fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.text((ai_x1 + 12, ge_y1 + 7), "🎮  Game Engine & GPU Graphics Driver", font=f_card_hdr, fill=(255, 255, 255))

    ge_bullets = [
        ("Game Loop:", "Deterministic 60 FPS Core Game Loop with Delta-Timing"),
        ("Compositor:", "Multi-Layer Background, Animated Sprites & UI Dialogue Box"),
        ("Asset Pipeline:", "Bootstraps assets/sprites.bin (24.5 KB) & palette.bin (768 B)"),
        ("Command FIFO:", "High-Level GPU Drawing API: CLEAR, SPRITE, LINE, RECT, SWAP"),
        ("Double-Buffer:", "Swaps Front/Back Framebuffer at VSync; Prevents Tearing"),
        ("Telemetry RX:", "Monitors FPGA Status Register (Busy Flags, Current Front Buffer)"),
    ]
    cur_y = ge_y1 + 42
    for b_title, b_desc in ge_bullets:
        draw.text((ai_x1 + 15, cur_y), b_title, font=f_body_bold, fill=accent_green)
        draw.text((ai_x1 + 120, cur_y), b_desc, font=f_body, fill=text_primary)
        cur_y += 24

    # Arrow Game Engine -> Peripherals
    draw_arrow(draw, (esp_x1 + (esp_x2 - esp_x1)//2, ge_y2), (esp_x1 + (esp_x2 - esp_x1)//2, ge_y2 + 25), color=wire_color)

    # --- ESP Subcard 3: Host Peripherals & Interfaces ---
    io_y1 = ge_y2 + 25
    io_y2 = io_y1 + 255
    draw.rounded_rectangle([ai_x1, io_y1, ai_x2, io_y2], radius=8, fill=subcard_bg, outline=subcard_border, width=1)
    draw.rounded_rectangle([ai_x1, io_y1, ai_x2, io_y1 + 32], radius=8, fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.rectangle([ai_x1, io_y1 + 20, ai_x2, io_y1 + 32], fill=(30, 58, 138) if theme == 'light' else (30, 41, 59))
    draw.text((ai_x1 + 12, io_y1 + 7), "🔌  Host Peripherals & I/O Subsystem", font=f_card_hdr, fill=(255, 255, 255))

    io_bullets = [
        ("USB Gamepad:", "USB OTG Host Interface (D-Pad, Investigation & Interrogate buttons)"),
        ("Serial Console:", "UART 115,200 Baud Real-Time Debug & Diagnostic Terminal"),
        ("SPI Master:", "Hardware SPI Controller with DMA (Transmits commands to FPGA)"),
        ("Memory Pool:", "512 KB Internal SRAM + 16 MB SPI Quad Flash Storage"),
    ]
    cur_y = io_y1 + 42
    for b_title, b_desc in io_bullets:
        draw.text((ai_x1 + 15, cur_y), b_title, font=f_body_bold, fill=accent_amber)
        draw.text((ai_x1 + 120, cur_y), b_desc, font=f_body, fill=text_primary)
        cur_y += 24

    # -------------------------------------------------------------------------
    # CENTER INTERCONNECT: SPI INTERFACE BUS
    # -------------------------------------------------------------------------
    spi_x1, spi_y1, spi_x2, spi_y2 = 740, 480, 1020, 720
    draw.rounded_rectangle([spi_x1, spi_y1, spi_x2, spi_y2], radius=10, fill=card_bg, outline=accent_amber, width=2)

    # Header
    draw.rounded_rectangle([spi_x1, spi_y1, spi_x2, spi_y1 + 36], radius=10, fill=accent_amber)
    draw.rectangle([spi_x1, spi_y1 + 20, spi_x2, spi_y1 + 36], fill=accent_amber)
    draw.text((spi_x1 + 25, spi_y1 + 8), "HIGH-SPEED SPI INTERFACE", font=f_card_hdr, fill=(255, 255, 255))

    # Details
    draw.text((spi_x1 + 15, spi_y1 + 48), "Protocol Clock: 4.0 MHz (Mode 0)", font=f_body_bold, fill=text_primary)
    draw.text((spi_x1 + 15, spi_y1 + 72), "Transmitted Signals (Host -> GPU):", font=f_body_bold, fill=accent_blue)
    draw.text((spi_x1 + 25, spi_y1 + 92), "• SCLK   : Synchronous SPI Clock", font=f_mono, fill=text_muted)
    draw.text((spi_x1 + 25, spi_y1 + 112), "• CS_N   : Active-Low Chip Select", font=f_mono, fill=text_muted)
    draw.text((spi_x1 + 25, spi_y1 + 132), "• MOSI   : GPU Command Stream", font=f_mono, fill=text_muted)

    draw.text((spi_x1 + 15, spi_y1 + 158), "Return Channel (GPU -> Host):", font=f_body_bold, fill=accent_green)
    draw.text((spi_x1 + 25, spi_y1 + 178), "• MISO   : Status & Telemetry", font=f_mono, fill=text_muted)
    draw.text((spi_x1 + 35, spi_y1 + 196), "(Clear, Blit, Line Busy, FrontBuf)", font=f_small, fill=text_muted)

    # Bus connecting arrows
    draw_arrow(draw, (esp_x2, 560), (spi_x1, 560), color=accent_blue, width=4, vertical=False)
    draw_arrow(draw, (spi_x1, 640), (esp_x2, 640), color=accent_green, width=4, vertical=False)
    draw_arrow(draw, (spi_x2, 600), (1040, 600), color=accent_amber, width=4, vertical=False)

    # -------------------------------------------------------------------------
    # RIGHT CONTAINER: GOWIN GW2AR-18C FPGA GPU
    # -------------------------------------------------------------------------
    fpga_x1, fpga_y1, fpga_x2, fpga_y2 = 1040, 110, 2140, 1160
    draw.rounded_rectangle([fpga_x1, fpga_y1, fpga_x2, fpga_y2], radius=12, fill=card_bg, outline=card_border, width=2)

    # FPGA Header Bar
    draw.rounded_rectangle([fpga_x1, fpga_y1, fpga_x2, fpga_y1 + 55], radius=12, fill=fpga_banner)
    draw.rectangle([fpga_x1, fpga_y1 + 40, fpga_x2, fpga_y1 + 55], fill=fpga_banner)
    draw.text((fpga_x1 + 20, fpga_y1 + 12), "GOWIN GW2AR-18C FPGA — CUSTOM 2D GPU CORE", font=f_title, fill=(255, 255, 255))
    draw.text((fpga_x1 + 720, fpga_y1 + 18), "20K LUT4 | 25.2 MHz / 27 MHz", font=f_subtitle, fill=(204, 251, 241))

    # --- FPGA Section 1: SPI Slave & Command Decoder ---
    dec_x1, dec_y1, dec_x2, dec_y2 = fpga_x1 + 20, fpga_y1 + 75, fpga_x2 - 20, fpga_y1 + 165
    draw.rounded_rectangle([dec_x1, dec_y1, dec_x2, dec_y2], radius=8, fill=subcard_bg, outline=subcard_border, width=1)
    draw.text((dec_x1 + 15, dec_y1 + 10), "📥  SPI Slave & GPU Command Decoder (cmd_decoder.v & spi_slave.v)", font=f_card_hdr, fill=text_primary)
    draw.text((dec_x1 + 15, dec_y1 + 35), "• Deserializes 32-bit packets  • Decodes Opcodes: CLEAR (0x01), SPRITE (0x02), LINE (0x03), RECT (0x04), SWAP (0x05)", font=f_body, fill=text_muted)
    draw.text((dec_x1 + 15, dec_y1 + 55), "• Controls Double-Buffer Front/Back page flip register  • Returns instantaneous hardware telemetry on MISO byte", font=f_body, fill=text_muted)

    # Branching arrows from Decoder to 3 Execution Engines
    dec_mid_y = dec_y2
    blit_cx = fpga_x1 + 180
    rast_cx = fpga_x1 + 540
    dma_cx  = fpga_x1 + 900

    draw_arrow(draw, (dec_x1 + 160, dec_mid_y), (blit_cx, dec_mid_y + 35), color=accent_blue, width=2)
    draw_arrow(draw, (dec_x1 + 520, dec_mid_y), (rast_cx, dec_mid_y + 35), color=accent_green, width=2)
    draw_arrow(draw, (dec_x1 + 880, dec_mid_y), (dma_cx, dec_mid_y + 35), color=accent_amber, width=2)

    # --- FPGA Section 2: Three Parallel Execution Engines ---
    eng_y1 = dec_mid_y + 35
    eng_y2 = eng_y1 + 140
    eng_w = 320

    # Engine 1: Blitter
    draw.rounded_rectangle([blit_cx - eng_w//2, eng_y1, blit_cx + eng_w//2, eng_y2], radius=8, fill=subcard_bg, outline=accent_blue, width=1)
    draw.text((blit_cx - eng_w//2 + 10, eng_y1 + 8), "⚡ Hardware Blitter (blitter.v)", font=f_card_sub, fill=accent_blue)
    draw.text((blit_cx - eng_w//2 + 10, eng_y1 + 32), "• 16x16, 16x32, 32x32 Sprites", font=f_small, fill=text_primary)
    draw.text((blit_cx - eng_w//2 + 10, eng_y1 + 52), "• Horizontal / Vertical Mirror (Flip)", font=f_small, fill=text_muted)
    draw.text((blit_cx - eng_w//2 + 10, eng_y1 + 72), "• Transparent Color Keying (Index 0)", font=f_small, fill=text_muted)
    draw.text((blit_cx - eng_w//2 + 10, eng_y1 + 92), "• DMA Read from SDRAM Sprite Bank", font=f_small, fill=text_muted)

    # Engine 2: Rasterizer
    draw.rounded_rectangle([rast_cx - eng_w//2, eng_y1, rast_cx + eng_w//2, eng_y2], radius=8, fill=subcard_bg, outline=accent_green, width=1)
    draw.text((rast_cx - eng_w//2 + 10, eng_y1 + 8), "📐 Hardware Rasterizer (rasterizer.v)", font=f_card_sub, fill=accent_green)
    draw.text((rast_cx - eng_w//2 + 10, eng_y1 + 32), "• Bresenham Line Drawing Engine", font=f_small, fill=text_primary)
    draw.text((rast_cx - eng_w//2 + 10, eng_y1 + 52), "• Solid & Hollow Rectangles", font=f_small, fill=text_muted)
    draw.text((rast_cx - eng_w//2 + 10, eng_y1 + 72), "• Fast Background Clear Engine", font=f_small, fill=text_muted)
    draw.text((rast_cx - eng_w//2 + 10, eng_y1 + 92), "• Integer Fixed-Point Arithmetic", font=f_small, fill=text_muted)

    # Engine 3: Asset & DMA Loader
    draw.rounded_rectangle([dma_cx - eng_w//2, eng_y1, dma_cx + eng_w//2, eng_y2], radius=8, fill=subcard_bg, outline=accent_amber, width=1)
    draw.text((dma_cx - eng_w//2 + 10, eng_y1 + 8), "📦 SDRAM Asset Loader & DMA", font=f_card_sub, fill=accent_amber)
    draw.text((dma_cx - eng_w//2 + 10, eng_y1 + 32), "• Bootstraps Sprite Sheet to SDRAM", font=f_small, fill=text_primary)
    draw.text((dma_cx - eng_w//2 + 10, eng_y1 + 52), "• Populates 256-Color Palette BRAM", font=f_small, fill=text_muted)
    draw.text((dma_cx - eng_w//2 + 10, eng_y1 + 72), "• 32-bit Word Alignment & Packing", font=f_small, fill=text_muted)
    draw.text((dma_cx - eng_w//2 + 10, eng_y1 + 92), "• Auto-Increment Memory Write", font=f_small, fill=text_muted)

    # Arrows from Engines down to Arbiter
    arb_mid_y = eng_y2 + 40
    draw_arrow(draw, (blit_cx, eng_y2), (blit_cx, arb_mid_y), color=wire_color, width=2)
    draw_arrow(draw, (rast_cx, eng_y2), (rast_cx, arb_mid_y), color=wire_color, width=2)
    draw_arrow(draw, (dma_cx, eng_y2), (dma_cx, arb_mid_y), color=wire_color, width=2)

    # --- FPGA Section 3: 4-Port Prioritized SDRAM Arbiter ---
    arb_x1, arb_y1, arb_x2, arb_y2 = fpga_x1 + 60, arb_mid_y, fpga_x2 - 60, arb_mid_y + 85
    draw.rounded_rectangle([arb_x1, arb_y1, arb_x2, arb_y2], radius=8, fill=subcard_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 15, arb_y1 + 10), "⚖️  4-Port Prioritized SDRAM Arbiter (sdram_arbiter.v)", font=f_card_hdr, fill=text_primary)
    draw.text((arb_x1 + 15, arb_y1 + 35), "Port 0: Video Scanout Engine (Strict Real-Time Priority 0 — Zero Glitch Tolerance)", font=f_body_bold, fill=accent_amber)
    draw.text((arb_x1 + 15, arb_y1 + 55), "Port 1: Blitter Engine  |  Port 2: Rasterizer Engine  |  Port 3: SPI Host Command Writer (Round-robin servicing on idle cycles)", font=f_body, fill=text_muted)

    # Arrow Arbiter -> SDRAM Controller
    draw_arrow(draw, (fpga_x1 + (fpga_x2 - fpga_x1)//2, arb_y2), (fpga_x1 + (fpga_x2 - fpga_x1)//2, arb_y2 + 30), color=wire_color, width=3)

    # --- FPGA Section 4: 64 Mbit SDR SDRAM Memory ---
    mem_y1 = arb_y2 + 30
    mem_y2 = mem_y1 + 130
    draw.rounded_rectangle([arb_x1, mem_y1, arb_x2, mem_y2], radius=8, fill=subcard_bg, outline=accent_amber, width=2)
    draw.text((arb_x1 + 15, mem_y1 + 10), "💾  64 Mbit (8 MB) 32-bit Embedded SDR SDRAM Controller (sdram_ctrl.v)", font=f_card_hdr, fill=accent_amber)

    # 3 Memory Banks Visualization
    b_w = 300
    b_h = 65
    b_y = mem_y1 + 45

    # Bank 1: Front Buffer
    draw.rounded_rectangle([arb_x1 + 20, b_y, arb_x1 + 20 + b_w, b_y + b_h], radius=6, fill=card_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 30, b_y + 8), "Framebuffer 0 (Front Display)", font=f_card_sub, fill=accent_blue)
    draw.text((arb_x1 + 30, b_y + 28), "640x480 @ 8bpp = 307.2 KB", font=f_mono, fill=text_primary)
    draw.text((arb_x1 + 30, b_y + 44), "Active Scanout Read Buffer", font=f_small, fill=text_muted)

    # Bank 2: Back Buffer
    draw.rounded_rectangle([arb_x1 + 350, b_y, arb_x1 + 350 + b_w, b_y + b_h], radius=6, fill=card_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 360, b_y + 8), "Framebuffer 1 (Back Render)", font=f_card_sub, fill=accent_green)
    draw.text((arb_x1 + 360, b_y + 28), "640x480 @ 8bpp = 307.2 KB", font=f_mono, fill=text_primary)
    draw.text((arb_x1 + 360, b_y + 44), "Active Host/GPU Draw Target", font=f_small, fill=text_muted)

    # Bank 3: Sprite Bank
    draw.rounded_rectangle([arb_x1 + 680, b_y, arb_x1 + 680 + b_w, b_y + b_h], radius=6, fill=card_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 690, b_y + 8), "Sprite & Tileset Bank", font=f_card_sub, fill=accent_amber)
    draw.text((arb_x1 + 690, b_y + 28), "Base 0x100000 (Up to 7.3 MB)", font=f_mono, fill=text_primary)
    draw.text((arb_x1 + 690, b_y + 44), "Characters, Tiles, UI Props", font=f_small, fill=text_muted)

    # Arrow SDRAM -> Scanout Engine
    draw_arrow(draw, (fpga_x1 + (fpga_x2 - fpga_x1)//2, mem_y2), (fpga_x1 + (fpga_x2 - fpga_x1)//2, mem_y2 + 30), color=wire_color, width=3)

    # --- FPGA Section 5: Video Scanout & Color Lookup (Palette) ---
    pipe_y1 = mem_y2 + 30
    pipe_y2 = pipe_y1 + 130

    # Block A: Video Scanout Engine
    pipe_w = 460
    draw.rounded_rectangle([arb_x1, pipe_y1, arb_x1 + pipe_w, pipe_y2], radius=8, fill=subcard_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 15, pipe_y1 + 10), "🖥️  Video Scanout Engine (video_scanout.v)", font=f_card_hdr, fill=text_primary)
    draw.text((arb_x1 + 15, pipe_y1 + 38), "• BL=4 Sequential 128-bit Burst Prefetch (Zero Starvation)", font=f_body_bold, fill=accent_amber)
    draw.text((arb_x1 + 15, pipe_y1 + 60), "• Dual Ping-Pong Line Buffer BRAMs (Active Line vs Prefetch Line)", font=f_body, fill=text_muted)
    draw.text((arb_x1 + 15, pipe_y1 + 82), "• Line budget: 480 prefetch cycles << 800 cycle scanline period", font=f_mono, fill=accent_green)
    draw.text((arb_x1 + 15, pipe_y1 + 104), "• Outputs 8-bit Indexed Color Stream to Palette Table", font=f_small, fill=text_muted)

    # Connecting Arrow Scanout -> Palette (8-bit index bus)
    draw_arrow(draw, (arb_x1 + pipe_w, pipe_y1 + 65), (arb_x1 + pipe_w + 70, pipe_y1 + 65), color=accent_amber, width=3, vertical=False)
    draw.text((arb_x1 + pipe_w + 8, pipe_y1 + 45), "8-bit Index", font=f_small, fill=accent_amber)

    # Block B: 256-Color Palette CLUT
    lut_x1 = arb_x1 + pipe_w + 70
    draw.rounded_rectangle([lut_x1, pipe_y1, fpga_x2 - 60, pipe_y2], radius=8, fill=subcard_bg, outline=accent_purple, width=1)
    draw.text((lut_x1 + 15, pipe_y1 + 10), "🎨  256-Color Palette CLUT (palette_lut.v)", font=f_card_hdr, fill=accent_purple)
    draw.text((lut_x1 + 15, pipe_y1 + 38), "• Dual-Port BRAM Color Lookup Table (256 x 24-bit RGB TrueColor)", font=f_body_bold, fill=text_primary)
    draw.text((lut_x1 + 15, pipe_y1 + 60), "• Translates 8-bit index into 24-bit TrueColor RGB (8:8:8)", font=f_body, fill=text_muted)
    draw.text((lut_x1 + 15, pipe_y1 + 82), "• Real-Time Dynamic Palette Switching for fades, damage, & lighting", font=f_body, fill=text_muted)
    draw.text((lut_x1 + 15, pipe_y1 + 104), "• Port A: SPI Host programming  |  Port B: Real-time scanout reader", font=f_small, fill=text_muted)

    # Arrow Palette -> TMDS Physical Layer
    draw_arrow(draw, (fpga_x1 + (fpga_x2 - fpga_x1)//2, pipe_y2), (fpga_x1 + (fpga_x2 - fpga_x1)//2, pipe_y2 + 25), color=wire_color, width=3)

    # --- FPGA Section 6: TMDS Encoders & SerDes PHY ---
    phy_y1 = pipe_y2 + 25
    phy_y2 = phy_y1 + 115
    draw.rounded_rectangle([arb_x1, phy_y1, fpga_x2 - 60, phy_y2], radius=8, fill=subcard_bg, outline=card_border, width=1)
    draw.text((arb_x1 + 15, phy_y1 + 10), "⚡  TMDS Encoders, Serializer & TLVDS PHY (tmds_encoder.v & hdmi_tx.v)", font=f_card_hdr, fill=text_primary)
    draw.text((arb_x1 + 15, pipe_y1 + 145), "• 3-Channel DVI 1.0 8b->10b DC-Balanced Encoders (R, G, B + Sync C0/C1)  • 5x Pixel Clock Serializer (126.0 MHz bit clock)", font=f_body, fill=text_muted)
    draw.text((arb_x1 + 15, pipe_y1 + 168), "• Gowin rPLL: 27.0 MHz Board Crystal -> 25.2 MHz Pixel Clock  • Gowin True-LVDS (TLVDS) Differential Output Buffers", font=f_body, fill=text_muted)
    draw.text((arb_x1 + 15, pipe_y1 + 190), "• Output Pins: Clock +/- (79/80), Data0 +/- (71/72), Data1 +/- (73/74), Data2 +/- (75/76)", font=f_mono_bold, fill=accent_purple)

    # Arrow FPGA Output -> Monitor
    draw_arrow(draw, (fpga_x1 + (fpga_x2 - fpga_x1)//2, fpga_y2), (fpga_x1 + (fpga_x2 - fpga_x1)//2, fpga_y2 + 35), color=accent_purple, width=4)

    # -------------------------------------------------------------------------
    # BOTTOM CONTAINER: HDMI / DVI MONITOR
    # -------------------------------------------------------------------------
    mon_x1, mon_y1, mon_x2, mon_y2 = 1320, 1195, 1860, 1260
    draw.rounded_rectangle([mon_x1, mon_y1, mon_x2, mon_y2], radius=8, fill=esp_banner if theme == 'light' else (30, 41, 59), outline=accent_purple, width=2)
    draw.text((mon_x1 + 40, mon_y1 + 10), "📺  HDMI / DVI MONITOR DISPLAY (640x480 @ 60 Hz Active Video)", font=f_card_hdr, fill=(255, 255, 255))
    draw.text((mon_x1 + 80, mon_y1 + 35), "Full 60 FPS Progressive Scan  |  256 TrueColor Palette  |  Zero Tearing", font=f_subtitle, fill=(219, 234, 254))

    # Save diagram
    suffix = "_dark.png" if theme == "dark" else ".png"
    out_path = os.path.join(DOCS_DIR, f"system_architecture_diagram{suffix}")
    img.save(out_path, dpi=(300, 300))
    print(f"Generated {theme} diagram: {out_path} ({w}x{h})")
    return out_path


def main():
    print("=" * 70)
    print("  GENERATING HIGH-RESOLUTION SYSTEM ARCHITECTURE DIAGRAMS  ")
    print("=" * 70)

    p_light = create_diagram(theme="light")
    p_dark = create_diagram(theme="dark")

    print("\n[SUCCESS] Both light and dark presentation diagrams rendered successfully!")


if __name__ == "__main__":
    main()
