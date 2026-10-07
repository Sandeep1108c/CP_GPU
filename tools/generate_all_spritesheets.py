#!/usr/bin/env python3
"""
Complete Sprite Sheet and Pixel Art Asset Generator for 'Find the Thief' RPG Console.
Custom FPGA GPU & Edge AI Project — Woxsen University

Generates:
1. Individual Character Sprite Sheets (16x32 walk/action frames + 32x32 portraits):
   - Detective Lelouch vi Britannia (Zero)
   - Shopkeeper Dazai Osamu
   - Guard Escanor
   - Farmer Roronoa Zoro
   - Kid Naruto Uzumaki
   - Old Man Master Roshi
2. World Environment Tileset (16x16 tiles: grass, path, water, brick, wood, vault, etc.)
3. Investigation Clues & Props (16x16 / 32x32: gold chest, coin sacks, cart, rope, cane tip, badge, straw, receipt, cider)
4. UI Elements (Dialogue box frames, hearts, interrogation magnifying glass, cursor)
5. Master Presentation Showcase Overview (scaled up with titles and labels)
6. FPGA Binary Assets:
   - assets/palette.bin (256-entry TrueColor CLUT)
   - assets/sprites.bin (8-bit indexed SDRAM binary)
   - firmware/include/all_sprites.h (C definitions and offsets)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
RAW_DIR = os.path.join(ASSETS_DIR, "raw")
BIN_DIR = os.path.join(ASSETS_DIR, "bin")
INCLUDE_DIR = os.path.join(PROJECT_ROOT, "firmware", "include")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)
os.makedirs(INCLUDE_DIR, exist_ok=True)

# Reserve index 0 for transparency
TRANSPARENT_COLOR = (0, 0, 0, 0)

# Build a comprehensive 256-color palette
def generate_master_palette():
    palette = [0] * (256 * 3)
    # 0: Transparent (Black)
    palette[0] = 0; palette[1] = 0; palette[2] = 0

    # 1..15: Classic 16 ANSI / VGA Colors
    vga16 = [
        (0x00, 0x00, 0xAA),  # 1: Dark Blue
        (0x00, 0xAA, 0x00),  # 2: Dark Green
        (0x00, 0xAA, 0xAA),  # 3: Cyan
        (0xAA, 0x00, 0x00),  # 4: Red
        (0xAA, 0x00, 0xAA),  # 5: Magenta
        (0xAA, 0x55, 0x00),  # 6: Brown
        (0xAA, 0xAA, 0xAA),  # 7: Light Gray
        (0x55, 0x55, 0x55),  # 8: Dark Gray
        (0x55, 0x55, 0xFF),  # 9: Bright Blue
        (0x55, 0xFF, 0x55),  # 10: Bright Green
        (0x55, 0xFF, 0xFF),  # 11: Bright Cyan
        (0xFF, 0x55, 0x55),  # 12: Bright Red
        (0xFF, 0x55, 0xFF),  # 13: Bright Magenta
        (0xFF, 0xFF, 0x55),  # 14: Bright Yellow
        (0xFF, 0xFF, 0xFF)   # 15: White
    ]
    for idx, (r, g, b) in enumerate(vga16, start=1):
        palette[idx * 3 + 0] = r
        palette[idx * 3 + 1] = g
        palette[idx * 3 + 2] = b

    # 16..231: 6x6x6 TrueColor Color Cube
    cube_levels = [0, 51, 102, 153, 204, 255]
    idx = 16
    for r in cube_levels:
        for g in cube_levels:
            for b in cube_levels:
                palette[idx * 3 + 0] = r
                palette[idx * 3 + 1] = g
                palette[idx * 3 + 2] = b
                idx += 1

    # 232..255: 24 Grayscale shades
    for i in range(24):
        gray = int(i * (255 / 23))
        palette[(232 + i) * 3 + 0] = gray
        palette[(232 + i) * 3 + 1] = gray
        palette[(232 + i) * 3 + 2] = gray

    return palette

def find_nearest_palette_index(r, g, b, palette):
    best_dist = float('inf')
    best_idx = 1
    for idx in range(1, 256):
        pr = palette[idx * 3 + 0]
        pg = palette[idx * 3 + 1]
        pb = palette[idx * 3 + 2]
        dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
        if dist < best_dist:
            best_dist = dist
            best_idx = idx
            if dist == 0:
                break
    return best_idx

def image_to_indexed_bytes(img, palette):
    w, h = img.size
    pixels = bytearray()
    for y in range(h):
        for x in range(w):
            rgba = img.getpixel((x, y))
            if len(rgba) == 4 and rgba[3] < 128:
                pixels.append(0)  # Transparent index
            else:
                r, g, b = rgba[:3]
                pixels.append(find_nearest_palette_index(r, g, b, palette))
    return pixels

# =============================================================================
# CHARACTER SPRITE GENERATORS (16x32 Bodies + 32x32 Face Portraits)
# =============================================================================

def draw_zero_frames():
    """Lelouch vi Britannia / Zero (Player Detective)"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Zero Helmet (Midnight blue / black with sweeping gold crescent & violet visor)
    d0.rectangle([5, 2, 10, 8], fill=(20, 20, 45, 255))
    d0.polygon([(3, 3), (5, 2), (5, 7)], fill=(218, 165, 32, 255)) # Gold left wing
    d0.polygon([(12, 3), (10, 2), (10, 7)], fill=(218, 165, 32, 255)) # Gold right wing
    d0.rectangle([6, 5, 9, 6], fill=(138, 43, 226, 255)) # Violet visor
    # High Collar Cape (Purple/Violet inside, Black outside, Gold trim)
    d0.polygon([(2, 9), (4, 15), (2, 27)], fill=(15, 15, 35, 255)) # Cape left
    d0.polygon([(13, 9), (11, 15), (13, 27)], fill=(15, 15, 35, 255)) # Cape right
    d0.rectangle([5, 9, 10, 12], fill=(218, 165, 32, 255)) # Gold collar/cravat
    # Torso: Black tunic with ornate gold embroidery
    d0.rectangle([5, 13, 10, 21], fill=(25, 25, 50, 255))
    d0.line([(7, 13), (7, 21)], fill=(218, 165, 32, 255))
    d0.line([(8, 13), (8, 21)], fill=(218, 165, 32, 255))
    d0.rectangle([4, 21, 11, 22], fill=(218, 165, 32, 255)) # Gold belt
    # Legs: White breeches & Black/Gold high boots
    d0.rectangle([5, 23, 7, 27], fill=(240, 240, 245, 255))
    d0.rectangle([8, 23, 10, 27], fill=(240, 240, 245, 255))
    d0.rectangle([5, 28, 7, 31], fill=(20, 20, 40, 255))
    d0.rectangle([8, 28, 10, 31], fill=(20, 20, 40, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 23, 11, 31], fill=(0, 0, 0, 0)) # Clear legs
    # Left step forward, right back
    d1.rectangle([4, 23, 6, 26], fill=(240, 240, 245, 255))
    d1.rectangle([9, 24, 11, 27], fill=(240, 240, 245, 255))
    d1.rectangle([3, 27, 6, 31], fill=(20, 20, 40, 255)) # Forward boot
    d1.rectangle([9, 28, 12, 31], fill=(20, 20, 40, 255)) # Rear boot
    d1.polygon([(1, 11), (3, 16), (1, 28)], fill=(15, 15, 35, 255)) # Billowing cape

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 23, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 23, 11, 26], fill=(240, 240, 245, 255))
    d2.rectangle([4, 24, 6, 27], fill=(240, 240, 245, 255))
    d2.rectangle([9, 27, 12, 31], fill=(20, 20, 40, 255))
    d2.rectangle([3, 28, 6, 31], fill=(20, 20, 40, 255))
    d2.polygon([(14, 11), (12, 16), (14, 28)], fill=(15, 15, 35, 255))

    # 4. Action / Deduce Pose (Zero dramatic arm outreach) (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    # Right arm raised dramatically
    d3.line([(10, 14), (14, 10)], fill=(218, 165, 32, 255), width=2)
    d3.rectangle([13, 8, 15, 10], fill=(240, 240, 245, 255)) # White glove pointing

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    # Background frame / aura
    dp.rectangle([2, 2, 29, 29], fill=(20, 10, 35, 255), outline=(218, 165, 32, 255))
    # Helmet & Crest
    dp.polygon([(16, 4), (8, 14), (24, 14)], fill=(15, 15, 40, 255))
    dp.polygon([(4, 8), (10, 6), (8, 16)], fill=(218, 165, 32, 255)) # Gold left wing
    dp.polygon([(27, 8), (21, 6), (23, 16)], fill=(218, 165, 32, 255)) # Gold right wing
    dp.rectangle([10, 14, 21, 22], fill=(20, 20, 45, 255))
    # Glowing Eye / Geass crest / Violet visor
    dp.ellipse([11, 15, 20, 19], fill=(147, 0, 211, 255))
    dp.point([(15, 17), (16, 17)], fill=(255, 50, 50, 255)) # Geass red gleam
    # High Imperial Collar
    dp.polygon([(4, 22), (10, 28), (4, 30)], fill=(218, 165, 32, 255))
    dp.polygon([(27, 22), (21, 28), (27, 30)], fill=(218, 165, 32, 255))
    dp.rectangle([12, 23, 19, 29], fill=(240, 240, 245, 255)) # Cravat
    dp.ellipse([14, 25, 17, 27], fill=(218, 165, 32, 255)) # Ruby brooch

    return [("HERO_ZERO_IDLE", f0), ("HERO_ZERO_WALK1", f1), ("HERO_ZERO_WALK2", f2),
            ("HERO_ZERO_ACTION", f3), ("HERO_ZERO_PORTRAIT", p)]

def draw_dazai_frames():
    """Dazai Osamu (Shopkeeper) — Bandages, sand coat, bolo tie, brown messy hair"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Messy dark brown hair
    d0.rectangle([4, 2, 11, 7], fill=(70, 45, 30, 255))
    d0.point([(3, 5), (12, 5), (4, 7), (11, 7)], fill=(70, 45, 30, 255))
    # Face & Bandages (Bandage on right cheek/eye)
    d0.rectangle([4, 6, 11, 12], fill=(255, 220, 190, 255)) # Skin
    d0.rectangle([8, 6, 11, 9], fill=(240, 240, 245, 255)) # Bandage patch
    d0.point([(6, 8)], fill=(50, 30, 20, 255)) # Left eye
    d0.line([(6, 11), (9, 10)], fill=(180, 100, 80, 255)) # Smirk
    # Neck bandages
    d0.rectangle([5, 12, 10, 13], fill=(240, 240, 245, 255))
    # Sand-colored trench coat & Dark vest
    d0.rectangle([3, 14, 12, 25], fill=(194, 160, 115, 255)) # Trench coat
    d0.rectangle([6, 14, 9, 21], fill=(40, 40, 50, 255)) # Dark vest
    d0.point([(7, 16), (8, 16)], fill=(0, 128, 128, 255)) # Turquoise bolo tie pendant
    # Bandaged wrists & hands in pockets
    d0.point([(3, 20), (12, 20)], fill=(240, 240, 245, 255))
    # Beige pants & dark brown shoes
    d0.rectangle([5, 25, 7, 29], fill=(180, 170, 150, 255))
    d0.rectangle([8, 25, 10, 29], fill=(180, 170, 150, 255))
    d0.rectangle([4, 29, 7, 31], fill=(50, 35, 25, 255))
    d0.rectangle([8, 29, 11, 31], fill=(50, 35, 25, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 25, 11, 31], fill=(0, 0, 0, 0))
    d1.rectangle([4, 25, 6, 28], fill=(180, 170, 150, 255))
    d1.rectangle([9, 26, 11, 29], fill=(180, 170, 150, 255))
    d1.rectangle([3, 28, 6, 31], fill=(50, 35, 25, 255))
    d1.rectangle([9, 29, 12, 31], fill=(50, 35, 25, 255))

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 25, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 25, 11, 28], fill=(180, 170, 150, 255))
    d2.rectangle([4, 26, 6, 29], fill=(180, 170, 150, 255))
    d2.rectangle([9, 28, 12, 31], fill=(50, 35, 25, 255))
    d2.rectangle([3, 29, 6, 31], fill=(50, 35, 25, 255))

    # 4. Holding Goods / Rope Pose (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    d3.ellipse([11, 16, 15, 22], fill=(160, 120, 60, 255), outline=(210, 180, 120, 255)) # Coil of rope

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    dp.rectangle([2, 2, 29, 29], fill=(30, 25, 20, 255), outline=(194, 160, 115, 255))
    # Hair
    dp.rectangle([8, 4, 23, 14], fill=(70, 45, 30, 255))
    dp.polygon([(6, 8), (8, 4), (6, 14)], fill=(70, 45, 30, 255))
    dp.polygon([(25, 8), (23, 4), (25, 14)], fill=(70, 45, 30, 255))
    # Face
    dp.rectangle([9, 11, 22, 21], fill=(255, 220, 190, 255))
    # Right eye wrapped in white bandages
    dp.rectangle([16, 11, 22, 16], fill=(240, 240, 245, 255))
    dp.line([(16, 13), (22, 13)], fill=(210, 210, 215, 255))
    # Left eye (dark brown, expressive)
    dp.ellipse([11, 13, 14, 16], fill=(50, 30, 20, 255))
    dp.point([(12, 14)], fill=(255, 255, 255, 255))
    # Witty cynic smirk
    dp.line([(13, 19), (18, 18)], fill=(160, 80, 60, 255), width=1)
    # Bandaged neck & Trench coat collar
    dp.rectangle([11, 22, 20, 24], fill=(240, 240, 245, 255))
    dp.polygon([(5, 22), (11, 27), (7, 30)], fill=(194, 160, 115, 255))
    dp.polygon([(26, 22), (20, 27), (24, 30)], fill=(194, 160, 115, 255))
    dp.ellipse([14, 26, 17, 28], fill=(0, 160, 160, 255)) # Bolo tie

    return [("NPC_DAZAI_IDLE", f0), ("NPC_DAZAI_WALK1", f1), ("NPC_DAZAI_WALK2", f2),
            ("NPC_DAZAI_ACTION", f3), ("NPC_DAZAI_PORTRAIT", p)]

def draw_escanor_frames():
    """Escanor (Guard Captain) — Golden armor, red cape, grand mustache, towering posture"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Golden hair & bushy mustache
    d0.rectangle([5, 2, 10, 6], fill=(218, 165, 32, 255)) # Golden hair
    d0.rectangle([4, 6, 11, 11], fill=(255, 215, 180, 255)) # Skin
    d0.point([(6, 8), (9, 8)], fill=(0, 100, 150, 255)) # Blue eyes
    d0.rectangle([5, 9, 10, 10], fill=(180, 115, 20, 255)) # Majestic mustache!
    # Golden Armor Pauldrons & Breastplate
    d0.rectangle([2, 11, 5, 16], fill=(255, 215, 0, 255)) # Left gold pauldron
    d0.rectangle([10, 11, 13, 16], fill=(255, 215, 0, 255)) # Right gold pauldron
    d0.rectangle([5, 11, 10, 21], fill=(230, 190, 0, 255)) # Golden cuirass
    d0.polygon([(7, 13), (8, 13), (7, 16)], fill=(178, 34, 34, 255)) # Lion emblem
    # Red royal cape behind
    d0.line([(1, 13), (1, 26)], fill=(178, 34, 34, 255))
    d0.line([(14, 13), (14, 26)], fill=(178, 34, 34, 255))
    # Armored tassets & Greaves
    d0.rectangle([4, 21, 11, 23], fill=(180, 140, 0, 255)) # Tassets
    d0.rectangle([5, 24, 7, 28], fill=(200, 200, 210, 255)) # Steel chainmail
    d0.rectangle([8, 24, 10, 28], fill=(200, 200, 210, 255))
    d0.rectangle([4, 28, 7, 31], fill=(255, 215, 0, 255)) # Golden sabatons
    d0.rectangle([8, 28, 11, 31], fill=(255, 215, 0, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 24, 11, 31], fill=(0, 0, 0, 0))
    d1.rectangle([4, 24, 6, 27], fill=(200, 200, 210, 255))
    d1.rectangle([9, 25, 11, 28], fill=(200, 200, 210, 255))
    d1.rectangle([3, 27, 6, 31], fill=(255, 215, 0, 255))
    d1.rectangle([9, 28, 12, 31], fill=(255, 215, 0, 255))

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 24, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 24, 11, 27], fill=(200, 200, 210, 255))
    d2.rectangle([4, 25, 6, 28], fill=(200, 200, 210, 255))
    d2.rectangle([9, 27, 12, 31], fill=(255, 215, 0, 255))
    d2.rectangle([3, 28, 6, 31], fill=(255, 215, 0, 255))

    # 4. Pride Stance / Axe at Shoulder (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    # Halberd / Divine Axe Rhitta shaft
    d3.line([(13, 2), (13, 30)], fill=(120, 80, 40, 255), width=2)
    d3.polygon([(11, 4), (15, 2), (15, 8)], fill=(255, 215, 0, 255)) # Axe blade

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    dp.rectangle([2, 2, 29, 29], fill=(25, 15, 10, 255), outline=(255, 215, 0, 255))
    # Golden hair parted
    dp.rectangle([9, 4, 22, 12], fill=(218, 165, 32, 255))
    dp.rectangle([10, 11, 21, 21], fill=(255, 215, 180, 255)) # Face
    dp.point([(12, 14), (19, 14)], fill=(0, 120, 200, 255)) # Proud blue eyes
    # Majestic Grand Mustache
    dp.polygon([(9, 18), (15, 16), (15, 20)], fill=(180, 115, 20, 255))
    dp.polygon([(22, 18), (16, 16), (16, 20)], fill=(180, 115, 20, 255))
    dp.rectangle([14, 17, 17, 19], fill=(180, 115, 20, 255))
    # Golden Gorget & Lion Crest
    dp.rectangle([7, 23, 24, 29], fill=(255, 215, 0, 255))
    dp.ellipse([13, 24, 18, 28], fill=(178, 34, 34, 255)) # Lion sun crest

    return [("NPC_ESCANOR_IDLE", f0), ("NPC_ESCANOR_WALK1", f1), ("NPC_ESCANOR_WALK2", f2),
            ("NPC_ESCANOR_ACTION", f3), ("NPC_ESCANOR_PORTRAIT", p)]

def draw_zoro_frames():
    """Roronoa Zoro (Farmer) — Spiky green hair, green haramaki sash, katanas/scythe, eye scar"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Marimo spiky green hair
    d0.rectangle([4, 2, 11, 7], fill=(46, 139, 87, 255))
    d0.point([(3, 3), (6, 1), (9, 1), (12, 3)], fill=(60, 179, 113, 255))
    # Rugged face & eye scar on left eye
    d0.rectangle([4, 6, 11, 12], fill=(245, 210, 175, 255))
    d0.point([(6, 8)], fill=(30, 30, 30, 255)) # Right eye open
    d0.line([(9, 7), (9, 9)], fill=(140, 50, 40, 255)) # Left eye scar!
    d0.line([(6, 11), (9, 11)], fill=(120, 80, 60, 255)) # Stern grimace
    # Open dark green farm coat / shirt
    d0.rectangle([3, 13, 12, 18], fill=(30, 70, 45, 255))
    d0.rectangle([6, 13, 9, 17], fill=(245, 210, 175, 255)) # Exposed chest
    # Iconic Green Haramaki (belly sash)
    d0.rectangle([4, 18, 11, 22], fill=(50, 205, 50, 255))
    # Three swords / tools at left hip
    d0.line([(2, 16), (2, 23)], fill=(220, 220, 220, 255))
    d0.line([(1, 18), (1, 24)], fill=(180, 0, 0, 255))
    # Black pants & boots
    d0.rectangle([5, 23, 7, 28], fill=(30, 30, 35, 255))
    d0.rectangle([8, 23, 10, 28], fill=(30, 30, 35, 255))
    d0.rectangle([4, 28, 7, 31], fill=(20, 20, 25, 255))
    d0.rectangle([8, 28, 11, 31], fill=(20, 20, 25, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 23, 11, 31], fill=(0, 0, 0, 0))
    d1.rectangle([4, 23, 6, 27], fill=(30, 30, 35, 255))
    d1.rectangle([9, 24, 11, 28], fill=(30, 30, 35, 255))
    d1.rectangle([3, 27, 6, 31], fill=(20, 20, 25, 255))
    d1.rectangle([9, 28, 12, 31], fill=(20, 20, 25, 255))

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 23, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 23, 11, 27], fill=(30, 30, 35, 255))
    d2.rectangle([4, 24, 6, 28], fill=(30, 30, 35, 255))
    d2.rectangle([9, 27, 12, 31], fill=(20, 20, 25, 255))
    d2.rectangle([3, 28, 6, 31], fill=(20, 20, 25, 255))

    # 4. Lost / Confused Scratching Head Pose (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    d3.line([(11, 14), (13, 8), (11, 5)], fill=(245, 210, 175, 255), width=2) # Hand behind head
    d3.point([(14, 4), (14, 5)], fill=(255, 255, 0, 255)) # Question sweat drop

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    dp.rectangle([2, 2, 29, 29], fill=(20, 30, 25, 255), outline=(46, 139, 87, 255))
    # Green cropped spiky hair
    dp.rectangle([8, 4, 23, 12], fill=(46, 139, 87, 255))
    dp.point([(6, 6), (9, 3), (15, 3), (21, 3), (24, 6)], fill=(60, 179, 113, 255))
    dp.rectangle([9, 10, 22, 22], fill=(245, 210, 175, 255)) # Face
    # Right eye piercing glare
    dp.rectangle([11, 13, 14, 15], fill=(30, 30, 30, 255))
    dp.point([(12, 14)], fill=(255, 255, 255, 255))
    # Left eye closed scar
    dp.line([(18, 11), (18, 17)], fill=(160, 50, 40, 255), width=1)
    # Gritting teeth smirk
    dp.rectangle([13, 19, 18, 20], fill=(255, 255, 255, 255))
    dp.line([(13, 19), (18, 19)], fill=(40, 40, 40, 255))
    # Dark green coat & haramaki collar
    dp.rectangle([6, 23, 25, 29], fill=(30, 70, 45, 255))
    dp.rectangle([12, 23, 19, 27], fill=(245, 210, 175, 255)) # Muscular neck/chest

    return [("NPC_ZORO_IDLE", f0), ("NPC_ZORO_WALK1", f1), ("NPC_ZORO_WALK2", f2),
            ("NPC_ZORO_ACTION", f3), ("NPC_ZORO_PORTRAIT", p)]

def draw_naruto_frames():
    """Naruto Uzumaki (The Kid) — Spiky blonde hair, Konoha headband, orange tracksuit, whiskers"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Spiky yellow hair
    d0.rectangle([4, 1, 11, 6], fill=(255, 215, 0, 255))
    d0.point([(3, 2), (5, 0), (8, 0), (10, 0), (12, 2)], fill=(255, 230, 50, 255))
    # Blue Headband with metal plate
    d0.rectangle([4, 6, 11, 8], fill=(30, 50, 130, 255))
    d0.rectangle([6, 6, 9, 7], fill=(200, 200, 210, 255)) # Silver metal plate
    # Face & whisker marks
    d0.rectangle([4, 8, 11, 13], fill=(255, 220, 180, 255))
    d0.point([(6, 10), (9, 10)], fill=(0, 120, 220, 255)) # Bright blue eyes
    d0.line([(4, 10), (5, 10)], fill=(180, 120, 80, 255)) # Left whiskers
    d0.line([(10, 10), (11, 10)], fill=(180, 120, 80, 255)) # Right whiskers
    d0.point([(7, 12), (8, 12)], fill=(200, 80, 80, 255)) # Grin
    # Orange Tracksuit with blue shoulders & white collar
    d0.rectangle([4, 14, 11, 15], fill=(255, 255, 255, 255)) # White fur collar
    d0.rectangle([3, 15, 12, 23], fill=(255, 100, 0, 255)) # Bright orange jacket
    d0.rectangle([3, 15, 5, 18], fill=(30, 50, 130, 255)) # Blue left shoulder
    d0.rectangle([10, 15, 12, 18], fill=(30, 50, 130, 255)) # Blue right shoulder
    d0.ellipse([7, 17, 8, 19], fill=(178, 34, 34, 255)) # Red Uzumaki swirl
    # Orange pants & blue ninja sandals
    d0.rectangle([5, 24, 7, 28], fill=(255, 100, 0, 255))
    d0.rectangle([8, 24, 10, 28], fill=(255, 100, 0, 255))
    d0.rectangle([5, 28, 7, 29], fill=(255, 255, 255, 255)) # Leg bandage
    d0.rectangle([4, 30, 7, 31], fill=(30, 50, 130, 255)) # Blue sandals
    d0.rectangle([8, 30, 11, 31], fill=(30, 50, 130, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 24, 11, 31], fill=(0, 0, 0, 0))
    d1.rectangle([4, 24, 6, 27], fill=(255, 100, 0, 255))
    d1.rectangle([9, 25, 11, 28], fill=(255, 100, 0, 255))
    d1.rectangle([3, 28, 6, 31], fill=(30, 50, 130, 255))
    d1.rectangle([9, 29, 12, 31], fill=(30, 50, 130, 255))

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 24, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 24, 11, 27], fill=(255, 100, 0, 255))
    d2.rectangle([4, 25, 6, 28], fill=(255, 100, 0, 255))
    d2.rectangle([9, 28, 12, 31], fill=(30, 50, 130, 255))
    d2.rectangle([3, 29, 6, 31], fill=(30, 50, 130, 255))

    # 4. Ninja Thumbs-Up "Dattebayo!" Pose (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    d3.line([(11, 17), (14, 15)], fill=(255, 100, 0, 255), width=2)
    d3.rectangle([13, 13, 15, 15], fill=(255, 220, 180, 255)) # Thumbs up fist

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    dp.rectangle([2, 2, 29, 29], fill=(35, 20, 10, 255), outline=(255, 100, 0, 255))
    # Spiky yellow hair
    dp.rectangle([7, 3, 24, 11], fill=(255, 215, 0, 255))
    dp.point([(5, 4), (8, 1), (13, 1), (18, 1), (23, 1), (26, 4)], fill=(255, 235, 80, 255))
    # Blue Headband & Metal Plate
    dp.rectangle([6, 9, 25, 14], fill=(30, 50, 130, 255))
    dp.rectangle([11, 10, 20, 13], fill=(210, 210, 220, 255)) # Metal Leaf plate
    dp.ellipse([14, 11, 17, 12], fill=(80, 80, 90, 255)) # Konoha spiral
    # Face & Whiskers
    dp.rectangle([8, 14, 23, 23], fill=(255, 220, 180, 255))
    dp.ellipse([10, 16, 13, 19], fill=(0, 140, 240, 255)) # Big blue eyes
    dp.ellipse([18, 16, 21, 19], fill=(0, 140, 240, 255))
    # Three whisker lines on each cheek
    dp.line([(8, 18), (10, 18)], fill=(160, 100, 60, 255))
    dp.line([(8, 20), (10, 20)], fill=(160, 100, 60, 255))
    dp.line([(21, 18), (23, 18)], fill=(160, 100, 60, 255))
    dp.line([(21, 20), (23, 20)], fill=(160, 100, 60, 255))
    # Wide grin
    dp.rectangle([13, 21, 18, 23], fill=(255, 255, 255, 255), outline=(180, 50, 50, 255))
    # Orange jacket collar
    dp.rectangle([6, 25, 25, 29], fill=(255, 100, 0, 255))
    dp.rectangle([10, 24, 21, 26], fill=(255, 255, 255, 255)) # White fleece

    return [("NPC_NARUTO_IDLE", f0), ("NPC_NARUTO_WALK1", f1), ("NPC_NARUTO_WALK2", f2),
            ("NPC_NARUTO_ACTION", f3), ("NPC_NARUTO_PORTRAIT", p)]

def draw_roshi_frames():
    """Master Roshi (Old Man) — Bald, white beard, dark sunglasses, orange aloha shirt, turtle shell"""
    # 1. Idle Down (16x32)
    f0 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(f0)
    # Bald head with age spots
    d0.ellipse([5, 2, 10, 7], fill=(245, 210, 180, 255))
    # Dark black sunglasses
    d0.rectangle([4, 7, 11, 9], fill=(20, 20, 20, 255))
    d0.point([(6, 8), (9, 8)], fill=(150, 150, 150, 255)) # Glass reflection
    # Big bushy white mustache and beard
    d0.rectangle([4, 10, 11, 14], fill=(250, 250, 250, 255))
    # Orange Aloha Shirt & Purple Turtle Shell backpack
    d0.rectangle([3, 15, 12, 22], fill=(255, 140, 0, 255)) # Orange shirt
    d0.point([(5, 17), (9, 19), (6, 21)], fill=(255, 255, 255, 255)) # Aloha flower patterns
    # Purple turtle shell edge visible
    d0.line([(2, 16), (2, 23)], fill=(128, 0, 128, 255), width=2)
    # Walking cane in hand
    d0.line([(13, 16), (13, 31)], fill=(139, 69, 19, 255), width=1)
    # White shorts & slippers
    d0.rectangle([5, 23, 7, 26], fill=(245, 245, 250, 255))
    d0.rectangle([8, 23, 10, 26], fill=(245, 245, 250, 255))
    d0.rectangle([5, 27, 7, 29], fill=(245, 210, 180, 255)) # Bare legs
    d0.rectangle([8, 27, 10, 29], fill=(245, 210, 180, 255))
    d0.rectangle([4, 30, 7, 31], fill=(139, 69, 19, 255)) # Sandals
    d0.rectangle([8, 30, 11, 31], fill=(139, 69, 19, 255))

    # 2. Walk Frame 1 (16x32)
    f1 = f0.copy()
    d1 = ImageDraw.Draw(f1)
    d1.rectangle([4, 27, 11, 31], fill=(0, 0, 0, 0))
    d1.rectangle([4, 27, 6, 29], fill=(245, 210, 180, 255))
    d1.rectangle([9, 28, 11, 30], fill=(245, 210, 180, 255))
    d1.rectangle([3, 29, 6, 31], fill=(139, 69, 19, 255))
    d1.rectangle([9, 30, 12, 31], fill=(139, 69, 19, 255))

    # 3. Walk Frame 2 (16x32)
    f2 = f0.copy()
    d2 = ImageDraw.Draw(f2)
    d2.rectangle([4, 27, 11, 31], fill=(0, 0, 0, 0))
    d2.rectangle([9, 27, 11, 29], fill=(245, 210, 180, 255))
    d2.rectangle([4, 28, 6, 30], fill=(245, 210, 180, 255))
    d2.rectangle([9, 29, 12, 31], fill=(139, 69, 19, 255))
    d2.rectangle([3, 30, 6, 31], fill=(139, 69, 19, 255))

    # 4. Chuckling Wisdom Pose (16x32)
    f3 = f0.copy()
    d3 = ImageDraw.Draw(f3)
    d3.line([(5, 17), (7, 12)], fill=(245, 210, 180, 255), width=2) # Stroking beard

    # 5. Face Portrait (32x32)
    p = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dp = ImageDraw.Draw(p)
    dp.rectangle([2, 2, 29, 29], fill=(30, 20, 30, 255), outline=(128, 0, 128, 255))
    # Shiny bald head
    dp.ellipse([8, 4, 23, 14], fill=(245, 210, 180, 255))
    dp.point([(12, 6), (13, 6)], fill=(255, 240, 220, 255)) # Head shine
    # Dark black sunglasses with white glare
    dp.rectangle([8, 12, 23, 17], fill=(20, 20, 20, 255))
    dp.line([(10, 13), (12, 13)], fill=(255, 255, 255, 255))
    dp.line([(18, 13), (20, 13)], fill=(255, 255, 255, 255))
    # Full white martial master beard
    dp.polygon([(7, 18), (15, 27), (24, 18)], fill=(250, 250, 250, 255))
    dp.polygon([(11, 18), (15, 22), (20, 18)], fill=(220, 220, 225, 255))
    # Orange aloha shirt collar & purple shell shoulder strap
    dp.rectangle([5, 25, 26, 29], fill=(255, 140, 0, 255))
    dp.rectangle([7, 24, 10, 29], fill=(128, 0, 128, 255)) # Shell strap

    return [("NPC_ROSHI_IDLE", f0), ("NPC_ROSHI_WALK1", f1), ("NPC_ROSHI_WALK2", f2),
            ("NPC_ROSHI_ACTION", f3), ("NPC_ROSHI_PORTRAIT", p)]

# =============================================================================
# ENVIRONMENT TILESET GENERATORS (16x16)
# =============================================================================

def draw_world_tiles():
    tiles = []

    # 1. Grass Tile
    t0 = Image.new("RGBA", (16, 16), (34, 139, 34, 255))
    d0 = ImageDraw.Draw(t0)
    d0.point([(2, 3), (6, 7), (12, 4), (10, 12), (4, 14), (8, 9), (14, 14)], fill=(50, 205, 50, 255))
    d0.point([(3, 9), (8, 2), (14, 11), (1, 12), (11, 7), (6, 13)], fill=(0, 100, 0, 255))
    tiles.append(("TILE_GRASS", t0))

    # 2. Wild Flower Grass
    t1 = t0.copy()
    d1 = ImageDraw.Draw(t1)
    d1.point([(5, 5), (11, 10)], fill=(255, 215, 0, 255)) # Yellow flowers
    d1.point([(12, 5), (4, 11)], fill=(255, 105, 180, 255)) # Pink flowers
    tiles.append(("TILE_FLOWER_GRASS", t1))

    # 3. Cobblestone / Stone Paver Path
    t2 = Image.new("RGBA", (16, 16), (128, 128, 128, 255))
    d2 = ImageDraw.Draw(t2)
    d2.rectangle([0, 0, 15, 15], outline=(80, 80, 80, 255))
    d2.line([(0, 8), (15, 8)], fill=(80, 80, 80, 255))
    d2.line([(8, 0), (8, 8)], fill=(80, 80, 80, 255))
    d2.line([(4, 8), (4, 15)], fill=(80, 80, 80, 255))
    d2.line([(12, 8), (12, 15)], fill=(80, 80, 80, 255))
    d2.point([(2, 2), (10, 2), (6, 10), (14, 10)], fill=(160, 160, 160, 255))
    tiles.append(("TILE_COBBLESTONE", t2))

    # 4. Animated Water Tile (Deep Blue with wave ripples)
    t3 = Image.new("RGBA", (16, 16), (30, 144, 255, 255))
    d3 = ImageDraw.Draw(t3)
    d3.line([(2, 4), (6, 4)], fill=(135, 206, 250, 255))
    d3.line([(9, 7), (13, 7)], fill=(135, 206, 250, 255))
    d3.line([(4, 11), (8, 11)], fill=(135, 206, 250, 255))
    d3.line([(11, 13), (14, 13)], fill=(0, 100, 200, 255))
    tiles.append(("TILE_WATER", t3))

    # 5. Red Brick Wall Tile
    t4 = Image.new("RGBA", (16, 16), (178, 34, 34, 255))
    d4 = ImageDraw.Draw(t4)
    d4.rectangle([0, 0, 15, 15], outline=(100, 20, 20, 255))
    d4.line([(0, 5), (15, 5)], fill=(90, 15, 15, 255))
    d4.line([(0, 10), (15, 10)], fill=(90, 15, 15, 255))
    d4.line([(7, 0), (7, 5)], fill=(90, 15, 15, 255))
    d4.line([(3, 5), (3, 10)], fill=(90, 15, 15, 255))
    d4.line([(11, 5), (11, 10)], fill=(90, 15, 15, 255))
    d4.line([(7, 10), (7, 15)], fill=(90, 15, 15, 255))
    tiles.append(("TILE_BRICK_WALL", t4))

    # 6. Wood Floor Planks (Shop interior)
    t5 = Image.new("RGBA", (16, 16), (160, 110, 60, 255))
    d5 = ImageDraw.Draw(t5)
    d5.line([(0, 5), (15, 5)], fill=(110, 70, 30, 255))
    d5.line([(0, 11), (15, 11)], fill=(110, 70, 30, 255))
    d5.line([(6, 0), (6, 5)], fill=(110, 70, 30, 255))
    d5.line([(12, 5), (12, 11)], fill=(110, 70, 30, 255))
    d5.line([(4, 11), (4, 15)], fill=(110, 70, 30, 255))
    tiles.append(("TILE_WOOD_PLANK", t5))

    # 7. Dirt / Valley Path
    t6 = Image.new("RGBA", (16, 16), (180, 140, 90, 255))
    d6 = ImageDraw.Draw(t6)
    d6.point([(3, 3), (9, 5), (13, 2), (6, 11), (12, 12)], fill=(140, 100, 60, 255))
    d6.point([(2, 9), (7, 7), (14, 8), (4, 14)], fill=(210, 175, 125, 255))
    tiles.append(("TILE_DIRT_PATH", t6))

    # 8. Council Treasury Vault Iron Door
    t7 = Image.new("RGBA", (16, 16), (80, 90, 100, 255))
    d7 = ImageDraw.Draw(t7)
    d7.rectangle([1, 1, 14, 14], outline=(40, 45, 50, 255))
    d7.ellipse([4, 4, 11, 11], outline=(218, 165, 32, 255), fill=(60, 70, 80, 255)) # Vault wheel
    d7.line([(7, 4), (7, 11)], fill=(218, 165, 32, 255))
    d7.line([(4, 7), (11, 7)], fill=(218, 165, 32, 255))
    d7.point([(12, 8)], fill=(255, 215, 0, 255)) # Brass keyhole
    tiles.append(("TILE_VAULT_DOOR", t7))

    return tiles

# =============================================================================
# INVESTIGATION CLUES & PROPS (16x16 / 32x32)
# =============================================================================

def draw_clues_and_props():
    props = []

    # 1. Stolen Treasury Gold Chest (16x16)
    p0 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(p0)
    d0.rectangle([2, 5, 13, 14], fill=(139, 69, 19, 255), outline=(218, 165, 32, 255))
    d0.rectangle([1, 4, 14, 7], fill=(160, 82, 45, 255), outline=(218, 165, 32, 255)) # Lid
    d0.rectangle([6, 7, 9, 10], fill=(255, 215, 0, 255)) # Padlock
    d0.point([(7, 8), (8, 8)], fill=(0, 0, 0, 255)) # Keyhole
    props.append(("PROP_GOLD_CHEST", p0))

    # 2. Canvas Coin Sack (16x16)
    p1 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(p1)
    d1.ellipse([2, 5, 13, 14], fill=(210, 180, 140, 255), outline=(160, 130, 90, 255))
    d1.rectangle([6, 3, 9, 5], fill=(180, 100, 40, 255)) # Tied knot
    d1.ellipse([6, 8, 9, 11], fill=(255, 215, 0, 255)) # Council seal stamp
    props.append(("PROP_COIN_SACK", p1))

    # 3. Wooden Handcart (32x32)
    p2 = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(p2)
    # Cart bed
    d2.rectangle([4, 8, 25, 20], fill=(160, 110, 60, 255), outline=(100, 60, 30, 255))
    d2.line([(4, 12), (25, 12)], fill=(100, 60, 30, 255))
    d2.line([(4, 16), (25, 16)], fill=(100, 60, 30, 255))
    # Handles
    d2.line([(25, 12), (30, 10)], fill=(120, 70, 35, 255), width=2)
    d2.line([(25, 16), (30, 14)], fill=(120, 70, 35, 255), width=2)
    # Wheels
    d2.ellipse([6, 18, 14, 26], fill=(80, 80, 80, 255), outline=(200, 200, 200, 255))
    d2.ellipse([17, 18, 25, 26], fill=(80, 80, 80, 255), outline=(200, 200, 200, 255))
    d2.point([(10, 22), (21, 22)], fill=(255, 215, 0, 255)) # Wheel hubs
    props.append(("PROP_HANDCART", p2))

    # 4. Hemp Rope & Bandages (16x16)
    p3 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(p3)
    d3.ellipse([1, 4, 10, 13], outline=(200, 160, 100, 255), width=2)
    d3.ellipse([3, 6, 8, 11], outline=(160, 120, 70, 255), width=1)
    d3.rectangle([8, 2, 14, 10], fill=(245, 245, 250, 255), outline=(200, 200, 210, 255)) # Bandage roll
    props.append(("PROP_ROPE_BANDAGE", p3))

    # 5. Broken Cane Tip (16x16 - Roshi Clue)
    p4 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(p4)
    d4.line([(3, 13), (12, 4)], fill=(139, 69, 19, 255), width=3)
    d4.rectangle([10, 2, 13, 5], fill=(200, 180, 140, 255)) # Bamboo joint
    d4.point([(2, 14), (3, 14)], fill=(180, 50, 50, 255)) # Splintered tip
    props.append(("PROP_CANE_TIP", p4))

    # 6. Brass Guard Crest Badge (16x16 - Escanor Clue)
    p5 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d5 = ImageDraw.Draw(p5)
    d5.polygon([(8, 2), (14, 5), (12, 13), (8, 15), (4, 13), (2, 5)], fill=(255, 215, 0, 255), outline=(180, 130, 0, 255))
    d5.ellipse([6, 6, 10, 10], fill=(178, 34, 34, 255)) # Red Lion sun crest
    props.append(("PROP_GUARD_BADGE", p5))

    # 7. Wheat Straw Stalk (16x16 - Zoro Clue)
    p6 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d6 = ImageDraw.Draw(p6)
    d6.line([(3, 14), (12, 3)], fill=(218, 165, 32, 255), width=2)
    d6.polygon([(10, 2), (14, 4), (11, 7)], fill=(240, 200, 80, 255))
    d6.polygon([(7, 6), (11, 8), (8, 11)], fill=(240, 200, 80, 255))
    props.append(("PROP_WHEAT_STRAW", p6))

    # 8. Torn Ledger Receipt (16x16 - Dazai Clue)
    p7 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d7 = ImageDraw.Draw(p7)
    d7.polygon([(3, 2), (13, 2), (13, 11), (10, 14), (7, 12), (3, 14)], fill=(250, 245, 220, 255), outline=(180, 160, 130, 255))
    d7.line([(5, 5), (11, 5)], fill=(60, 60, 60, 255))
    d7.line([(5, 7), (10, 7)], fill=(60, 60, 60, 255))
    d7.line([(5, 9), (8, 9)], fill=(180, 30, 30, 255)) # Red signature stamp
    props.append(("PROP_LEDGER_RECEIPT", p7))

    # 9. Spiced Cider Flask (16x16 - Drugged Watchman Flask)
    p8 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d8 = ImageDraw.Draw(p8)
    d8.rectangle([6, 2, 9, 4], fill=(160, 120, 80, 255)) # Cork
    d8.ellipse([3, 5, 12, 14], fill=(70, 130, 180, 255), outline=(30, 60, 90, 255)) # Glass
    d8.rectangle([5, 8, 10, 12], fill=(200, 100, 30, 255)) # Spiced cider fluid
    props.append(("PROP_CIDER_FLASK", p8))

    return props

# =============================================================================
# UI ELEMENTS GENERATORS (16x16 / 32x32)
# =============================================================================

def draw_ui_elements():
    ui = []

    # 1. Full Heart (16x16)
    u0 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(u0)
    d0.polygon([(8, 13), (2, 7), (2, 4), (5, 2), (8, 5), (11, 2), (14, 4), (14, 7)], fill=(255, 30, 30, 255), outline=(150, 0, 0, 255))
    d0.point([(4, 4), (5, 4)], fill=(255, 180, 180, 255)) # Gloss highlight
    ui.append(("UI_HEART_FULL", u0))

    # 2. Empty Heart (16x16)
    u1 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(u1)
    d1.polygon([(8, 13), (2, 7), (2, 4), (5, 2), (8, 5), (11, 2), (14, 4), (14, 7)], fill=(60, 60, 70, 255), outline=(120, 120, 130, 255))
    ui.append(("UI_HEART_EMPTY", u1))

    # 3. Interrogation Magnifying Glass Icon (16x16)
    u2 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(u2)
    d2.ellipse([2, 2, 10, 10], outline=(218, 165, 32, 255), fill=(200, 240, 255, 180), width=2)
    d2.line([(9, 9), (14, 14)], fill=(139, 69, 19, 255), width=3)
    ui.append(("UI_MAGNIFIER", u2))

    # 4. Dialogue Box Border Slice / Corner (16x16)
    u3 = Image.new("RGBA", (16, 16), (20, 25, 40, 255))
    d3 = ImageDraw.Draw(u3)
    d3.rectangle([0, 0, 15, 15], outline=(218, 165, 32, 255))
    d3.rectangle([2, 2, 13, 13], outline=(70, 90, 130, 255))
    ui.append(("UI_DIALOGUE_BORDER", u3))

    return ui

# =============================================================================
# MASTER SHOWCASE OVERVIEW (PRESENTATION CARD)
# =============================================================================

def build_presentation_showcase(all_sprites):
    """
    Creates a large, beautifully laid-out 800x480 presentation poster
    showcasing all characters, portraits, world tiles, investigation clues,
    and UI elements with clean labels.
    """
    canvas = Image.new("RGB", (960, 540), (16, 22, 34)) # Elegant dark navy
    draw = ImageDraw.Draw(canvas)

    # Decorative header
    draw.rectangle([0, 0, 960, 50], fill=(24, 34, 52))
    draw.line([(0, 50), (960, 50)], fill=(218, 165, 32), width=2)

    # Title & Subtitle
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 20)
        font_med = ImageFont.truetype("arial.ttf", 13)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font_large = font_med = font_small = ImageFont.load_default()

    draw.text((20, 12), "CUSTOM FPGA GPU — 'FIND THE THIEF' COMPLETE ASSET ARCHITECTURE", fill=(255, 215, 0), font=font_large)
    draw.text((700, 16), "WOXSEN UNIVERSITY | 60 FPS", fill=(180, 200, 230), font=font_med)

    sprite_dict = {s["name"]: s["img"] for s in all_sprites}

    # Section 1: Character Roster (Hero & 5 NPCs)
    draw.rectangle([15, 60, 620, 310], fill=(20, 28, 44), outline=(45, 60, 85))
    draw.text((25, 65), "CAST ROSTER: DETECTIVE ZERO & 5 ANIME-VOICED NPCS (16x32 & 32x32 PORTRAITS)", fill=(100, 200, 255), font=font_med)

    characters = [
        ("Zero (Detective)", "Lelouch vi Britannia", "HERO_ZERO_PORTRAIT", "HERO_ZERO_IDLE", "HERO_ZERO_ACTION"),
        ("Shopkeeper", "Dazai Osamu", "NPC_DAZAI_PORTRAIT", "NPC_DAZAI_IDLE", "NPC_DAZAI_ACTION"),
        ("Watch Guard", "Escanor (Lion of Pride)", "NPC_ESCANOR_PORTRAIT", "NPC_ESCANOR_IDLE", "NPC_ESCANOR_ACTION"),
        ("Farmer", "Roronoa Zoro", "NPC_ZORO_PORTRAIT", "NPC_ZORO_IDLE", "NPC_ZORO_ACTION"),
        ("The Kid", "Naruto Uzumaki", "NPC_NARUTO_PORTRAIT", "NPC_NARUTO_IDLE", "NPC_NARUTO_ACTION"),
        ("Old Hermit", "Master Roshi", "NPC_ROSHI_PORTRAIT", "NPC_ROSHI_IDLE", "NPC_ROSHI_ACTION"),
    ]

    for idx, (role, name, port_name, idle_name, act_name) in enumerate(characters):
        cx = 25 + (idx % 3) * 195
        cy = 90 + (idx // 3) * 105

        draw.rectangle([cx, cy, cx + 185, cy + 95], fill=(28, 38, 58), outline=(60, 80, 110))

        # 32x32 Portrait scaled 1.5x -> 48x48
        if port_name in sprite_dict:
            port = sprite_dict[port_name].resize((48, 48), Image.Resampling.NEAREST)
            canvas.paste(port, (cx + 6, cy + 8), port)

        # 16x32 Sprites scaled 1.5x -> 24x48
        if idle_name in sprite_dict:
            idle = sprite_dict[idle_name].resize((24, 48), Image.Resampling.NEAREST)
            canvas.paste(idle, (cx + 60, cy + 8), idle)

        if act_name in sprite_dict:
            act = sprite_dict[act_name].resize((24, 48), Image.Resampling.NEAREST)
            canvas.paste(act, (cx + 88, cy + 8), act)

        # Text labels
        draw.text((cx + 6, cy + 60), role, fill=(255, 215, 0), font=font_small)
        draw.text((cx + 6, cy + 74), name[:18], fill=(220, 220, 230), font=font_small)

    # Section 2: Environment Tileset (16x16 Scaled 2x -> 32x32)
    draw.rectangle([645, 60, 945, 230], fill=(20, 28, 44), outline=(45, 60, 85))
    draw.text((655, 65), "WORLD ENVIRONMENT TILESET (16x16)", fill=(100, 200, 255), font=font_med)

    world_tile_names = [
        ("TILE_GRASS", "Grass"), ("TILE_FLOWER_GRASS", "Meadow"),
        ("TILE_COBBLESTONE", "Stone Path"), ("TILE_WATER", "Lake/Water"),
        ("TILE_BRICK_WALL", "Brick Wall"), ("TILE_WOOD_PLANK", "Wood Floor"),
        ("TILE_DIRT_PATH", "Dirt Trail"), ("TILE_VAULT_DOOR", "Iron Vault")
    ]

    for idx, (t_name, label) in enumerate(world_tile_names):
        tx = 655 + (idx % 4) * 70
        ty = 90 + (idx // 4) * 65

        if t_name in sprite_dict:
            tile_img = sprite_dict[t_name].resize((32, 32), Image.Resampling.NEAREST)
            canvas.paste(tile_img, (tx + 12, ty), tile_img)
        draw.text((tx + 6, ty + 36), label, fill=(200, 210, 220), font=font_small)

    # Section 3: Investigation Clues & Props
    draw.rectangle([645, 240, 945, 410], fill=(20, 28, 44), outline=(45, 60, 85))
    draw.text((655, 245), "INVESTIGATION CLUES & PROPS", fill=(100, 200, 255), font=font_med)

    clue_names = [
        ("PROP_GOLD_CHEST", "Vault Chest"), ("PROP_COIN_SACK", "Tax Sack"),
        ("PROP_ROPE_BANDAGE", "Rope & Cloth"), ("PROP_CANE_TIP", "Cane Tip"),
        ("PROP_GUARD_BADGE", "Brass Crest"), ("PROP_WHEAT_STRAW", "Farm Straw"),
        ("PROP_LEDGER_RECEIPT", "Torn Bill"), ("PROP_CIDER_FLASK", "Cider Flask")
    ]

    for idx, (c_name, label) in enumerate(clue_names):
        cx = 655 + (idx % 4) * 70
        cy = 270 + (idx // 4) * 65
        if c_name in sprite_dict:
            clue_img = sprite_dict[c_name].resize((32, 32), Image.Resampling.NEAREST)
            canvas.paste(clue_img, (cx + 12, cy), clue_img)
        draw.text((cx + 6, cy + 36), label, fill=(200, 210, 220), font=font_small)

    # Section 4: Game Architecture & Technical HUD
    draw.rectangle([15, 380, 620, 520], fill=(20, 28, 44), outline=(45, 60, 85))
    draw.text((25, 385), "HARDWARE PIPELINE & HUD INTEGRATION", fill=(100, 200, 255), font=font_med)

    # Mock in-game dialogue box preview
    draw.rectangle([30, 410, 400, 505], fill=(12, 18, 30), outline=(218, 165, 32), width=2)
    # Paste Zero Portrait
    if "HERO_ZERO_PORTRAIT" in sprite_dict:
        dp = sprite_dict["HERO_ZERO_PORTRAIT"].resize((44, 44), Image.Resampling.NEAREST)
        canvas.paste(dp, (36, 425), dp)
    draw.text((90, 418), "DETECTIVE ZERO [Lelouch]:", fill=(255, 215, 0), font=font_med)
    draw.text((90, 438), "\"Who gave you the authority to question my deduction?!", fill=(230, 230, 240), font=font_small)
    draw.text((90, 453), "The missing duplicate brass key was in your post drawer,\",", fill=(230, 230, 240), font=font_small)
    draw.text((90, 468), "and the spiked cider proves an inside job!\"", fill=(230, 230, 240), font=font_small)

    # Heart & UI icons preview
    if "UI_HEART_FULL" in sprite_dict:
        h1 = sprite_dict["UI_HEART_FULL"].resize((20, 20), Image.Resampling.NEAREST)
        canvas.paste(h1, (30, 485), h1)
        canvas.paste(h1, (54, 485), h1)
    if "UI_HEART_EMPTY" in sprite_dict:
        h0 = sprite_dict["UI_HEART_EMPTY"].resize((20, 20), Image.Resampling.NEAREST)
        canvas.paste(h0, (78, 485), h0)
    if "UI_MAGNIFIER" in sprite_dict:
        mag = sprite_dict["UI_MAGNIFIER"].resize((20, 20), Image.Resampling.NEAREST)
        canvas.paste(mag, (360, 482), mag)

    # Hardware Specs Summary on poster
    draw.text((420, 410), "• Display: 640x480 @ 60Hz HDMI", fill=(180, 200, 220), font=font_small)
    draw.text((420, 426), "• SDRAM: 8MB 32-bit (BL=4 Burst)", fill=(180, 200, 220), font=font_small)
    draw.text((420, 442), "• Blitter: 2D Sprite Engine (Flip-X)", fill=(180, 200, 220), font=font_small)
    draw.text((420, 458), "• AI Engine: 4.8M INT8 nanoGPT", fill=(180, 200, 220), font=font_small)
    draw.text((420, 474), "• Microcontroller: ESP32-S3 SPI", fill=(180, 200, 220), font=font_small)
    draw.text((420, 490), "• Memory: 256-Color CLUT (BRAM)", fill=(180, 200, 220), font=font_small)

    # Section 5: Handcart Prop (32x32 scaled 2x -> 64x64)
    draw.rectangle([645, 420, 945, 520], fill=(20, 28, 44), outline=(45, 60, 85))
    draw.text((655, 425), "SPECIAL VEHICLE / PROP: MILL CART", fill=(100, 200, 255), font=font_med)
    if "PROP_HANDCART" in sprite_dict:
        cart = sprite_dict["PROP_HANDCART"].resize((64, 64), Image.Resampling.NEAREST)
        canvas.paste(cart, (670, 445), cart)
    draw.text((750, 450), "32x32 Transport Cart", fill=(255, 215, 0), font=font_small)
    draw.text((750, 468), "Used to haul gold chests", fill=(200, 210, 220), font=font_small)
    draw.text((750, 484), "to the old mill silo.", fill=(200, 210, 220), font=font_small)

    return canvas

# =============================================================================
# MAIN EXPORT ROUTINE
# =============================================================================

def main():
    print("=================================================================")
    print("   GENERATING SPRITESHEETS & ASSET PIPELINE FOR FPGA + ESP32    ")
    print("=================================================================")

    # 1. Master Palette
    palette = generate_master_palette()
    palette_path = os.path.join(ASSETS_DIR, "palette.bin")
    with open(palette_path, "wb") as f:
        f.write(bytearray(palette))
    print(f"[1/6] Master Palette generated: {palette_path} (768 bytes, 256 colors)")

    # 2. Gather All Sprites
    all_sprites = []

    # Characters
    char_groups = [
        ("hero_zero", draw_zero_frames()),
        ("npc_dazai", draw_dazai_frames()),
        ("npc_escanor", draw_escanor_frames()),
        ("npc_zoro", draw_zoro_frames()),
        ("npc_naruto", draw_naruto_frames()),
        ("npc_roshi", draw_roshi_frames())
    ]

    for char_key, frames in char_groups:
        # Save individual character sprite sheet image
        # Arrange horizontally: 4 body frames (16x32) + 1 portrait (32x32) -> total width = 16*4 + 32 = 96, height = 32
        sheet = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        cur_x = 0
        for name, img in frames:
            sheet.paste(img, (cur_x, 0), img)
            all_sprites.append({"name": name, "img": img, "width": img.size[0], "height": img.size[1]})
            cur_x += img.size[0]

        char_sheet_path = os.path.join(RAW_DIR, f"{char_key}_spritesheet.png")
        sheet.save(char_sheet_path)
        print(f"      Saved {char_sheet_path}")

    # World Tiles
    world_tiles = draw_world_tiles()
    tiles_sheet = Image.new("RGBA", (16 * len(world_tiles), 16), (0, 0, 0, 0))
    for idx, (name, img) in enumerate(world_tiles):
        tiles_sheet.paste(img, (idx * 16, 0), img)
        all_sprites.append({"name": name, "img": img, "width": 16, "height": 16})
    tiles_sheet_path = os.path.join(RAW_DIR, "tileset_world.png")
    tiles_sheet.save(tiles_sheet_path)
    print(f"[2/6] World Tileset saved: {tiles_sheet_path} ({len(world_tiles)} tiles)")

    # Clues & Props
    clues_and_props = draw_clues_and_props()
    # Calculate width
    total_w = sum(img.size[0] for _, img in clues_and_props)
    props_sheet = Image.new("RGBA", (total_w, 32), (0, 0, 0, 0))
    cur_x = 0
    for name, img in clues_and_props:
        props_sheet.paste(img, (cur_x, 0), img)
        all_sprites.append({"name": name, "img": img, "width": img.size[0], "height": img.size[1]})
        cur_x += img.size[0]
    props_sheet_path = os.path.join(RAW_DIR, "clues_and_props.png")
    props_sheet.save(props_sheet_path)
    print(f"[3/6] Investigation Props saved: {props_sheet_path} ({len(clues_and_props)} props)")

    # UI Elements
    ui_elements = draw_ui_elements()
    ui_w = sum(img.size[0] for _, img in ui_elements)
    ui_sheet = Image.new("RGBA", (ui_w, 16), (0, 0, 0, 0))
    cur_x = 0
    for name, img in ui_elements:
        ui_sheet.paste(img, (cur_x, 0), img)
        all_sprites.append({"name": name, "img": img, "width": img.size[0], "height": img.size[1]})
        cur_x += img.size[0]
    ui_sheet_path = os.path.join(RAW_DIR, "ui_elements.png")
    ui_sheet.save(ui_sheet_path)
    print(f"[4/6] UI Elements saved: {ui_sheet_path} ({len(ui_elements)} elements)")

    # 3. Build Presentation Showcase Poster
    showcase_img = build_presentation_showcase(all_sprites)
    showcase_path = os.path.join(RAW_DIR, "master_spritesheet_overview.png")
    showcase_img.save(showcase_path)
    print(f"[5/6] Master Presentation Overview saved: {showcase_path} (960x540 poster)")

    # 4. Compile All into FPGA SDRAM Indexed Binary
    sprites_bin_path = os.path.join(ASSETS_DIR, "sprites.bin")
    header_path = os.path.join(INCLUDE_DIR, "all_sprites.h")

    total_sdram_bytes = 0
    with open(sprites_bin_path, "wb") as f_bin:
        for s in all_sprites:
            indexed_data = image_to_indexed_bytes(s["img"], palette)
            s["data"] = indexed_data
            s["offset"] = total_sdram_bytes
            s["size_bytes"] = len(indexed_data)
            f_bin.write(indexed_data)
            total_sdram_bytes += len(indexed_data)

    print(f"[6/6] Compiled SDRAM binary: {sprites_bin_path} ({total_sdram_bytes} bytes for {len(all_sprites)} sprites)")

    # 5. Write C Header for ESP32 Firmware
    with open(header_path, "w") as f_h:
        f_h.write("/**\n")
        f_h.write(" * @file all_sprites.h\n")
        f_h.write(" * @brief Complete Sprite Metadata and Memory Map for Tang Nano 20K GPU\n")
        f_h.write(" * Auto-generated by tools/generate_all_spritesheets.py\n")
        f_h.write(" */\n\n")
        f_h.write("#ifndef ALL_SPRITES_H\n")
        f_h.write("#define ALL_SPRITES_H\n\n")
        f_h.write("#include <stdint.h>\n\n")
        f_h.write(f"#define TOTAL_SPRITE_COUNT      {len(all_sprites)}\n")
        f_h.write(f"#define TOTAL_SPRITE_SDRAM_BYTES {total_sdram_bytes}\n")
        f_h.write("#define SDRAM_SPRITE_BASE_ADDR   0x100000\n\n")

        # Enum IDs
        f_h.write("typedef enum {\n")
        for idx, s in enumerate(all_sprites):
            f_h.write(f"    SPRITE_ID_{s['name']} = {idx},\n")
        f_h.write("} sprite_id_t;\n\n")

        # Sprite Metadata Struct
        f_h.write("typedef struct {\n")
        f_h.write("    const char* name;\n")
        f_h.write("    uint16_t id;\n")
        f_h.write("    uint16_t width;\n")
        f_h.write("    uint16_t height;\n")
        f_h.write("    uint32_t sdram_offset;\n")
        f_h.write("    uint32_t size_bytes;\n")
        f_h.write("} sprite_meta_t;\n\n")

        f_h.write("static const sprite_meta_t SPRITE_MANIFEST[] = {\n")
        for idx, s in enumerate(all_sprites):
            f_h.write(f'    {{"{s["name"]}", {idx}, {s["width"]}, {s["height"]}, 0x{s["offset"]:06X}, {s["size_bytes"]}}},\n')
        f_h.write("};\n\n")
        f_h.write("#endif // ALL_SPRITES_H\n")

    print(f"      C Header exported: {header_path}")
    print("\n[SUCCESS] All spritesheets, assets, poster, binaries, and C headers generated successfully!\n")

if __name__ == "__main__":
    main()
