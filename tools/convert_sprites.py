#!/usr/bin/env python3
# =============================================================================
# Tool: 2D Sprite Asset Conversion Pipeline (convert_sprites.py)
# Project: Custom FPGA-Based GPU — Woxsen University
# Description:
#   Converts sprite art (PNG/JPG/RGBA) into FPGA-ready indexed 8-bit binaries
#   and C header definitions for the ESP32-S3 firmware.
#
#   Generates:
#     1. assets/palette.bin         - 256-entry TrueColor palette (768 bytes RGB)
#     2. assets/sprites.bin         - Raw indexed 8-bit sprite pixels for SDRAM
#     3. firmware/include/sprites.h - C constants, enums, dimensions, and arrays
# =============================================================================

import os
import sys
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
INCLUDE_DIR = os.path.join(PROJECT_ROOT, "firmware", "include")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(INCLUDE_DIR, exist_ok=True)

# Reserve index 0 for transparency (black/alpha key)
TRANSPARENT_COLOR = (0, 0, 0)

# Build a standard palette:
# Index 0: Transparent (0, 0, 0)
# Index 1-15: Standard 16 ANSI/VGA colors
# Index 16-231: 6x6x6 TrueColor RGB cube
# Index 232-255: 24 Grayscale shades
def generate_standard_palette():
    palette = [0] * (256 * 3)
    # 0: Transparent
    palette[0] = 0; palette[1] = 0; palette[2] = 0

    # 1..15: Classic VGA 16
    vga16 = [
        (0x00, 0x00, 0xAA), # 1: Blue
        (0x00, 0xAA, 0x00), # 2: Green
        (0x00, 0xAA, 0xAA), # 3: Cyan
        (0xAA, 0x00, 0x00), # 4: Red
        (0xAA, 0x00, 0xAA), # 5: Magenta
        (0xAA, 0x55, 0x00), # 6: Brown
        (0xAA, 0xAA, 0xAA), # 7: Light Gray
        (0x55, 0x55, 0x55), # 8: Dark Gray
        (0x55, 0x55, 0xFF), # 9: Bright Blue
        (0x55, 0xFF, 0x55), # 10: Bright Green
        (0x55, 0xFF, 0xFF), # 11: Bright Cyan
        (0xFF, 0x55, 0x55), # 12: Bright Red
        (0xFF, 0x55, 0xFF), # 13: Bright Magenta
        (0xFF, 0xFF, 0x55), # 14: Bright Yellow
        (0xFF, 0xFF, 0xFF)  # 15: White
    ]
    for idx, (r, g, b) in enumerate(vga16, start=1):
        palette[idx * 3 + 0] = r
        palette[idx * 3 + 1] = g
        palette[idx * 3 + 2] = b

    # 16..231: 6x6x6 color cube
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

# Map an RGB tuple to nearest palette index (1..255)
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

# Procedural demo pixel art generator
def create_demo_sprites(palette):
    sprites = [] # List of dict: {name, width, height, data: bytes}

    # 1. 16x16 World Tiles (Grass, Stone, Water, Wall)
    # Tile 0: Grass Tile
    img_grass = Image.new("RGBA", (16, 16), (34, 139, 34, 255))
    d = ImageDraw.Draw(img_grass)
    d.point([(2, 3), (6, 7), (12, 4), (10, 12), (4, 14)], fill=(50, 205, 50, 255))
    d.point([(3, 9), (8, 2), (14, 11), (1, 12)], fill=(0, 100, 0, 255))

    # Tile 1: Stone Tile
    img_stone = Image.new("RGBA", (16, 16), (128, 128, 128, 255))
    d = ImageDraw.Draw(img_stone)
    d.rectangle([0, 0, 15, 15], outline=(80, 80, 80, 255))
    d.line([(0, 8), (15, 8)], fill=(80, 80, 80, 255))
    d.line([(8, 0), (8, 8)], fill=(80, 80, 80, 255))
    d.line([(4, 8), (4, 15)], fill=(80, 80, 80, 255))

    # Tile 2: Water Tile
    img_water = Image.new("RGBA", (16, 16), (30, 144, 255, 255))
    d = ImageDraw.Draw(img_water)
    d.line([(2, 4), (6, 4)], fill=(135, 206, 250, 255))
    d.line([(8, 10), (13, 10)], fill=(135, 206, 250, 255))

    # Tile 3: Brick Wall Tile
    img_wall = Image.new("RGBA", (16, 16), (178, 34, 34, 255))
    d = ImageDraw.Draw(img_wall)
    d.rectangle([0, 0, 15, 15], outline=(100, 20, 20, 255))
    d.line([(0, 5), (15, 5)], fill=(100, 20, 20, 255))
    d.line([(0, 10), (15, 10)], fill=(100, 20, 20, 255))

    tile_imgs = [("TILE_GRASS", img_grass), ("TILE_STONE", img_stone),
                 ("TILE_WATER", img_water), ("TILE_WALL", img_wall)]

    for name, img in tile_imgs:
        pixels = bytearray()
        for y in range(16):
            for x in range(16):
                r, g, b, a = img.getpixel((x, y))
                if a < 128:
                    pixels.append(0)
                else:
                    pixels.append(find_nearest_palette_index(r, g, b, palette))
        sprites.append({"name": name, "width": 16, "height": 16, "data": pixels})

    # 2. 16x32 Character Walking Sprites (Hero/Player: Down, Up, Right)
    # Character Down Frame 1
    img_char_down1 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_char_down1)
    # Head & Hair (Yellow hair, skin face)
    d.rectangle([4, 2, 11, 7], fill=(255, 215, 0, 255))  # Gold hair
    d.rectangle([4, 6, 11, 13], fill=(255, 218, 185, 255)) # Skin
    d.point([(6, 9), (9, 9)], fill=(0, 0, 139, 255))       # Blue eyes
    # Torso (Orange martial arts gi)
    d.rectangle([3, 14, 12, 23], fill=(255, 69, 0, 255))   # Orange gi
    d.rectangle([5, 15, 10, 20], fill=(0, 0, 139, 255))    # Blue undershirt
    d.rectangle([3, 21, 12, 23], fill=(0, 0, 139, 255))    # Blue belt
    # Legs & Boots
    d.rectangle([4, 24, 6, 30], fill=(255, 69, 0, 255))    # Left leg
    d.rectangle([9, 24, 11, 29], fill=(255, 69, 0, 255))   # Right leg (stepped)
    d.rectangle([3, 29, 7, 31], fill=(0, 0, 139, 255))     # Blue boots
    d.rectangle([8, 28, 12, 30], fill=(0, 0, 139, 255))

    # Character Down Frame 2
    img_char_down2 = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_char_down2)
    d.rectangle([4, 2, 11, 7], fill=(255, 215, 0, 255))
    d.rectangle([4, 6, 11, 13], fill=(255, 218, 185, 255))
    d.point([(6, 9), (9, 9)], fill=(0, 0, 139, 255))
    d.rectangle([3, 14, 12, 23], fill=(255, 69, 0, 255))
    d.rectangle([5, 15, 10, 20], fill=(0, 0, 139, 255))
    d.rectangle([3, 21, 12, 23], fill=(0, 0, 139, 255))
    d.rectangle([4, 24, 6, 29], fill=(255, 69, 0, 255))
    d.rectangle([9, 24, 11, 30], fill=(255, 69, 0, 255))
    d.rectangle([3, 28, 7, 30], fill=(0, 0, 139, 255))
    d.rectangle([8, 29, 12, 31], fill=(0, 0, 139, 255))

    char_imgs = [("PLAYER_DOWN_0", img_char_down1), ("PLAYER_DOWN_1", img_char_down2)]

    for name, img in char_imgs:
        pixels = bytearray()
        for y in range(32):
            for x in range(16):
                r, g, b, a = img.getpixel((x, y))
                if a < 128:
                    pixels.append(0) # Transparency
                else:
                    pixels.append(find_nearest_palette_index(r, g, b, palette))
        sprites.append({"name": name, "width": 16, "height": 32, "data": pixels})

    # 3. 32x32 Boss Dragon / Demon Avatar
    img_boss = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_boss)
    # Head & Horns
    d.polygon([(16, 2), (6, 12), (26, 12)], fill=(178, 34, 34, 255))
    d.polygon([(4, 4), (8, 12), (2, 10)], fill=(255, 215, 0, 255)) # Left horn
    d.polygon([(28, 4), (24, 12), (30, 10)], fill=(255, 215, 0, 255)) # Right horn
    d.ellipse([10, 10, 14, 14], fill=(255, 255, 0, 255)) # Glowing yellow eyes
    d.ellipse([18, 10, 22, 14], fill=(255, 255, 0, 255))
    d.point([(12, 12), (20, 12)], fill=(0, 0, 0, 255))
    # Body & Claws
    d.rectangle([8, 14, 24, 26], fill=(139, 0, 0, 255))
    d.rectangle([12, 16, 20, 24], fill=(255, 69, 0, 255))
    d.polygon([(4, 26), (10, 30), (4, 31)], fill=(255, 215, 0, 255))
    d.polygon([(28, 26), (22, 30), (28, 31)], fill=(255, 215, 0, 255))

    pixels = bytearray()
    for y in range(32):
        for x in range(32):
            r, g, b, a = img_boss.getpixel((x, y))
            if a < 128:
                pixels.append(0)
            else:
                pixels.append(find_nearest_palette_index(r, g, b, palette))
    sprites.append({"name": "BOSS_DRAGON", "width": 32, "height": 32, "data": pixels})

    return sprites

def main():
    print("========================================================")
    print("   2D SPRITE ASSET CONVERSION PIPELINE (FPGA + ESP32)   ")
    print("========================================================")

    # 1. Generate standard 256-color palette
    palette = generate_standard_palette()
    palette_bin_path = os.path.join(ASSETS_DIR, "palette.bin")
    with open(palette_bin_path, "wb") as f:
        f.write(bytearray(palette))
    print(f"Generated {palette_bin_path} ({len(palette)} bytes: 256 RGB entries)")

    # 2. Generate Demo Sprites
    sprites = create_demo_sprites(palette)

    sprites_bin_path = os.path.join(ASSETS_DIR, "sprites.bin")
    header_path = os.path.join(INCLUDE_DIR, "sprites.h")

    total_bytes = 0
    with open(sprites_bin_path, "wb") as f_bin:
        for s in sprites:
            s["offset"] = total_bytes
            f_bin.write(s["data"])
            total_bytes += len(s["data"])

    print(f"Generated {sprites_bin_path} ({total_bytes} bytes for SDRAM upload)")

    # 3. Generate C Header for Firmware
    with open(header_path, "w") as f_h:
        f_h.write("/**\n")
        f_h.write(" * @file sprites.h\n")
        f_h.write(" * @brief Auto-generated 2D Sprite Definitions and Metadata\n")
        f_h.write(" * Generated by tools/convert_sprites.py\n")
        f_h.write(" */\n\n")
        f_h.write("#ifndef SPRITES_H\n")
        f_h.write("#define SPRITES_H\n\n")
        f_h.write("#include <stdint.h>\n\n")

        f_h.write(f"#define TOTAL_SPRITES_COUNT  {len(sprites)}\n")
        f_h.write(f"#define TOTAL_SPRITES_BYTES  {total_bytes}\n\n")

        # Enum IDs
        f_h.write("// Sprite Asset IDs\n")
        f_h.write("typedef enum {\n")
        for i, s in enumerate(sprites):
            f_h.write(f"    SPRITE_ID_{s['name']} = {i},\n")
        f_h.write("} sprite_id_t;\n\n")

        # Metadata Table
        f_h.write("// Sprite Metadata Structure\n")
        f_h.write("typedef struct {\n")
        f_h.write("    const char *name;\n")
        f_h.write("    uint16_t id;\n")
        f_h.write("    uint16_t width;\n")
        f_h.write("    uint16_t height;\n")
        f_h.write("    uint32_t sdram_offset;\n")
        f_h.write("    uint16_t byte_length;\n")
        f_h.write("} sprite_meta_t;\n\n")

        f_h.write("static const sprite_meta_t SPRITE_METADATA[] = {\n")
        for i, s in enumerate(sprites):
            f_h.write(f"    {{\"{s['name']}\", {i}, {s['width']}, {s['height']}, {s['offset']}, {len(s['data'])}}},\n")
        f_h.write("};\n\n")

        # Raw Sprite Pixel Arrays
        f_h.write("// Embedded Sprite Byte Arrays for Flash Upload\n")
        for s in sprites:
            f_h.write(f"static const uint8_t SPRITE_DATA_{s['name']}[{len(s['data'])}] = {{\n    ")
            for idx, b in enumerate(s['data']):
                f_h.write(f"0x{b:02X}, ")
                if (idx + 1) % 16 == 0 and (idx + 1) < len(s['data']):
                    f_h.write("\n    ")
            f_h.write("\n};\n\n")

        # Embedded Palette Array
        f_h.write("// Pre-computed 256-Color Palette (768 bytes: R, G, B triplets)\n")
        f_h.write("static const uint8_t DEFAULT_GPU_PALETTE[768] = {\n    ")
        for idx, b in enumerate(palette):
            f_h.write(f"0x{b:02X}, ")
            if (idx + 1) % 16 == 0 and (idx + 1) < len(palette):
                f_h.write("\n    ")
        f_h.write("\n};\n\n")

        f_h.write("#endif // SPRITES_H\n")

    print(f"Generated {header_path} with {len(sprites)} sprites and full C arrays.")
    print("Done! All sprite assets ready for ESP32 and FPGA.")

if __name__ == "__main__":
    main()
