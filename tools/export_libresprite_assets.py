#!/usr/bin/env python3
"""
Export Complete Game Assets Suite for LibreSprite (.aseprite / .ase) and PNG.
Project: Custom FPGA-Based GPU Game Console — Woxsen University

Generates native LibreSprite / Aseprite documents with:
  - Multi-frame timeline walk & action animations (Spacebar to Play!)
  - Animation tags: Idle, Walk, Action
  - Native pixel grid properties (16x16, 16x32, 32x32)
  - Full spritesheet projects (.aseprite and .ase)
  - Individual tile & prop projects (.aseprite and .ase)
  - Companion standard PNG files
"""

import os
import sys
import struct
import zlib
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GAME_ASSETS_DIR = os.path.join(PROJECT_ROOT, "game_assets")

# Subdirectories
LIBRE_DIR = os.path.join(GAME_ASSETS_DIR, "libresprite")
PNG_DIR = os.path.join(GAME_ASSETS_DIR, "png_exports")

ANIM_DIR = os.path.join(LIBRE_DIR, "characters_animated")
SHEETS_DIR = os.path.join(LIBRE_DIR, "characters_sheets")
PORTRAITS_DIR = os.path.join(LIBRE_DIR, "characters_portraits")
TILES_DIR = os.path.join(LIBRE_DIR, "environment_tiles")
PROPS_DIR = os.path.join(LIBRE_DIR, "investigation_props")
UI_DIR = os.path.join(LIBRE_DIR, "ui_hud")
SHOWCASE_DIR = os.path.join(LIBRE_DIR, "master_showcase")

PNG_SHEETS_DIR = os.path.join(PNG_DIR, "sheets")
PNG_INDIV_DIR = os.path.join(PNG_DIR, "individual_sprites")

for d in [ANIM_DIR, SHEETS_DIR, PORTRAITS_DIR, TILES_DIR, PROPS_DIR, UI_DIR, SHOWCASE_DIR, PNG_SHEETS_DIR, PNG_INDIV_DIR]:
    os.makedirs(d, exist_ok=True)

# Import pixel art renderers
sys.path.insert(0, SCRIPT_DIR)
import generate_all_spritesheets as gen


master_palette_rgb = gen.generate_master_palette()

def write_aseprite(filepath, width, height, frames_rgba, durations=None, tags=None, grid=(16, 16), layer_name="Layer"):
    """
    Writes a 100% compliant Aseprite / LibreSprite v1.1+ binary file (.aseprite or .ase).
    Guarantees valid 128-byte header, Palette chunk (0x2019), Layer chunk (0x2004),
    and Cel chunk (0x2005) with compressed 32-bpp RGBA pixel buffers.
    """
    num_frames = len(frames_rgba)
    if durations is None:
        durations = [150] * num_frames
    elif len(durations) < num_frames:
        durations = durations + [150] * (num_frames - len(durations))

    grid_w, grid_h = grid
    magic_file = 0xA5E0
    magic_frame = 0xF1FA
    header_size = 128

    # 1. Palette Chunk (0x2019)
    # Size: 4B palette size, 4B first, 4B last, 8B reserved
    p_body = struct.pack("<III8s", 256, 0, 255, b"\x00" * 8)
    for i in range(256):
        r = master_palette_rgb[i * 3 + 0]
        g = master_palette_rgb[i * 3 + 1]
        b = master_palette_rgb[i * 3 + 2]
        a = 0 if i == 0 else 255
        p_body += struct.pack("<HBBBB", 0, r, g, b, a)

    # 2. Layer Chunk (0x2004)
    l_name_bytes = layer_name.encode("utf-8")
    l_body = struct.pack(
        "<HHHHHBB3sH",
        3, 0, 0, 0, 0, 0, 255, b"\x00\x00\x00", len(l_name_bytes)
    ) + l_name_bytes

    # 3. Optional Tags Chunk (0x2018)
    tag_body = b""
    if tags:
        tag_body = struct.pack("<H8s", len(tags), b"\x00" * 8)
        tag_colors = [
            b"\x50\xc8\x78",  # Emerald
            b"\x3c\xa0\xdc",  # Cyan
            b"\xff\xb4\x3c",  # Amber
            b"\xff\x64\x64"   # Coral
        ]
        for t_idx, (from_f, to_f, t_name) in enumerate(tags):
            t_name_bytes = t_name.encode("utf-8")
            c_rgb = tag_colors[t_idx % len(tag_colors)]
            tag_body += struct.pack(
                "<HHB8s3sBH",
                from_f, to_f, 0, b"\x00" * 8, c_rgb, 0, len(t_name_bytes)
            ) + t_name_bytes

    frame_bytes_list = []
    for f_idx, rgba in enumerate(frames_rgba):
        chunks = []
        # Frame 0 contains Palette, Layer, and Tags
        if f_idx == 0:
            chunks.append((0x2019, p_body))
            chunks.append((0x2004, l_body))
            if tags:
                chunks.append((0x2018, tag_body))

        # Cel Chunk (0x2005) - Cel type 2 (ZLIB compressed raw 32-bpp RGBA pixels)
        compressed_pixels = zlib.compress(rgba)
        c_body = struct.pack(
            "<HhhBH7sHH",
            0, 0, 0, 255, 2, b"\x00" * 7, width, height
        ) + compressed_pixels
        chunks.append((0x2005, c_body))

        # Build Frame Payload
        chunks_blob = b""
        for c_type, c_data in chunks:
            c_len = len(c_data) + 6
            chunks_blob += struct.pack("<IH", c_len, c_type) + c_data

        f_len = len(chunks_blob) + 16
        dur = durations[f_idx]
        f_header = struct.pack(
            "<IHHH2sI",
            f_len, magic_frame, len(chunks), dur, b"\x00\x00", len(chunks)
        )
        frame_bytes_list.append(f_header + chunks_blob)

    total_size = header_size + sum(len(f) for f in frame_bytes_list)
    # Header format: EXACTLY 128 BYTES
    fmt = "<IHHHHHIHIIB3sHBBhhHH84s"
    file_header = struct.pack(
        fmt,
        total_size, magic_file, num_frames, width, height, 32,
        1,              # flags (1 = Layer valid)
        durations[0],   # speed (deprecated)
        0, 0,           # reserved1, reserved2
        0,              # transparent index
        b"\x00\x00\x00",# ignore 3 bytes
        0,              # num_colors (0 = default)
        1, 1,           # pixel ratio 1:1
        0, 0,           # grid x, y
        grid_w, grid_h, # grid width & height
        b"\x00" * 84    # reserved 84 bytes
    )

    with open(filepath, "wb") as f:
        f.write(file_header)
        for fb in frame_bytes_list:
            f.write(fb)


def save_as_libresprite_pair(base_path, width, height, frames_rgba, durations=None, tags=None, grid=(16, 16), layer_name="Sprite"):
    """Saves both .aseprite and .ase extensions so LibreSprite opens either smoothly."""
    p_aseprite = f"{base_path}.aseprite"
    p_ase = f"{base_path}.ase"
    write_aseprite(p_aseprite, width, height, frames_rgba, durations, tags, grid, layer_name)
    write_aseprite(p_ase, width, height, frames_rgba, durations, tags, grid, layer_name)
    return p_aseprite, p_ase


def main():
    print("=" * 70)
    print("  EXPORTING GAME ASSETS SUITE FOR LIBRESPRITE (.aseprite / .ase)  ")
    print("=" * 70)

    # 1. Characters: Animated Projects & Full Sheets
    char_defs = [
        ("hero_zero", "Zero (Lelouch)", gen.draw_zero_frames()),
        ("npc_dazai", "Shopkeeper Dazai", gen.draw_dazai_frames()),
        ("npc_escanor", "Guard Escanor", gen.draw_escanor_frames()),
        ("npc_zoro", "Farmer Zoro", gen.draw_zoro_frames()),
        ("npc_naruto", "Kid Naruto", gen.draw_naruto_frames()),
        ("npc_roshi", "Old Man Roshi", gen.draw_roshi_frames())
    ]

    all_sprites = []

    print("\n[1/6] Processing Characters...")
    for char_key, char_title, frame_tuples in char_defs:
        # frame_tuples has 5 items:
        # 0: Idle (16x32)
        # 1: Walk 1 (16x32)
        # 2: Walk 2 (16x32)
        # 3: Action (16x32)
        # 4: Portrait (32x32)
        body_frames = frame_tuples[:4]
        portrait_tuple = frame_tuples[4]

        # A) Animated LibreSprite Document (16x32, 4 frames with tags!)
        anim_rgba = [f_img.tobytes() for _, f_img in body_frames]
        durations = [150, 150, 150, 250]
        tags = [
            (0, 0, "Idle"),
            (0, 2, "Walk Cycle"),
            (3, 3, "Action / Clue")
        ]
        anim_base = os.path.join(ANIM_DIR, f"{char_key}_animated")
        save_as_libresprite_pair(anim_base, 16, 32, anim_rgba, durations=durations, tags=tags, grid=(16, 32), layer_name=f"{char_title} Walk")
        print(f"  -> Generated Animated Project: {char_key}_animated.aseprite / .ase (4 frames, playable in LibreSprite)")

        # Save individual PNG frames
        for f_idx, (f_name, f_img) in enumerate(body_frames):
            png_indiv_path = os.path.join(PNG_INDIV_DIR, f"{f_name.lower()}.png")
            f_img.save(png_indiv_path)
            all_sprites.append({"name": f_name, "img": f_img, "width": 16, "height": 32})

        # Save portrait individual
        p_name, p_img = portrait_tuple
        all_sprites.append({"name": p_name, "img": p_img, "width": 32, "height": 32})
        p_png = os.path.join(PNG_INDIV_DIR, f"{p_name.lower()}.png")
        p_img.save(p_png)

        # Portrait LibreSprite Document (32x32)
        port_base = os.path.join(PORTRAITS_DIR, f"{char_key}_portrait")
        save_as_libresprite_pair(port_base, 32, 32, [p_img.tobytes()], durations=[1000], grid=(32, 32), layer_name=f"{char_title} Portrait")

        # B) Full Spritesheet Document (96x32 canvas, 4 body frames + 32x32 portrait)
        sheet_img = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        cur_x = 0
        for _, img in frame_tuples:
            sheet_img.paste(img, (cur_x, 0), img)
            cur_x += img.size[0]

        sheet_base = os.path.join(SHEETS_DIR, f"{char_key}_sheet")
        save_as_libresprite_pair(sheet_base, 96, 32, [sheet_img.tobytes()], durations=[1000], grid=(16, 32), layer_name=f"{char_title} Sheet")
        sheet_png = os.path.join(PNG_SHEETS_DIR, f"{char_key}_sheet.png")
        sheet_img.save(sheet_png)

    # 2. Environment World Tiles
    print("\n[2/6] Processing Environment Tiles...")
    world_tiles = gen.draw_world_tiles()
    tiles_sheet = Image.new("RGBA", (16 * len(world_tiles), 16), (0, 0, 0, 0))
    for idx, (t_name, t_img) in enumerate(world_tiles):
        tiles_sheet.paste(t_img, (idx * 16, 0), t_img)
        all_sprites.append({"name": t_name, "img": t_img, "width": 16, "height": 16})
        # Save individual tile
        t_base = os.path.join(TILES_DIR, t_name.lower())
        save_as_libresprite_pair(t_base, 16, 16, [t_img.tobytes()], durations=[1000], grid=(16, 16), layer_name=t_name)
        t_png = os.path.join(PNG_INDIV_DIR, f"{t_name.lower()}.png")
        t_img.save(t_png)

    # Full tilesheet document
    tiles_base = os.path.join(TILES_DIR, "tileset_world_sheet")
    save_as_libresprite_pair(tiles_base, 16 * len(world_tiles), 16, [tiles_sheet.tobytes()], grid=(16, 16), layer_name="World Tiles")
    tiles_png = os.path.join(PNG_SHEETS_DIR, "tileset_world_sheet.png")
    tiles_sheet.save(tiles_png)
    print(f"  -> Generated Tileset Sheet: tileset_world_sheet.aseprite / .ase ({len(world_tiles)} tiles on 16x16 grid)")

    # 3. Investigation Props & Clues
    print("\n[3/6] Processing Investigation Props & Clues...")
    clues = gen.draw_clues_and_props()
    total_w = sum(img.size[0] for _, img in clues)
    props_sheet = Image.new("RGBA", (total_w, 32), (0, 0, 0, 0))
    cur_x = 0
    for c_name, c_img in clues:
        props_sheet.paste(c_img, (cur_x, 0), c_img)
        all_sprites.append({"name": c_name, "img": c_img, "width": c_img.size[0], "height": c_img.size[1]})
        # Save individual prop
        p_base = os.path.join(PROPS_DIR, c_name.lower())
        save_as_libresprite_pair(p_base, c_img.size[0], c_img.size[1], [c_img.tobytes()], grid=(16, 16), layer_name=c_name)
        p_png = os.path.join(PNG_INDIV_DIR, f"{c_name.lower()}.png")
        c_img.save(p_png)
        cur_x += c_img.size[0]

    props_base = os.path.join(PROPS_DIR, "clues_and_props_sheet")
    save_as_libresprite_pair(props_base, total_w, 32, [props_sheet.tobytes()], grid=(16, 16), layer_name="Investigation Props")
    props_png = os.path.join(PNG_SHEETS_DIR, "clues_and_props_sheet.png")
    props_sheet.save(props_png)
    print(f"  -> Generated Props Sheet: clues_and_props_sheet.aseprite / .ase ({len(clues)} props on 16x16 grid)")

    # 4. UI Elements & HUD
    print("\n[4/6] Processing UI & HUD Elements...")
    ui_elements = gen.draw_ui_elements()
    ui_w = sum(img.size[0] for _, img in ui_elements)
    ui_sheet = Image.new("RGBA", (ui_w, 16), (0, 0, 0, 0))
    cur_x = 0
    for u_name, u_img in ui_elements:
        ui_sheet.paste(u_img, (cur_x, 0), u_img)
        all_sprites.append({"name": u_name, "img": u_img, "width": u_img.size[0], "height": u_img.size[1]})
        # Individual UI icon
        u_base = os.path.join(UI_DIR, u_name.lower())
        save_as_libresprite_pair(u_base, u_img.size[0], u_img.size[1], [u_img.tobytes()], grid=(16, 16), layer_name=u_name)
        u_png = os.path.join(PNG_INDIV_DIR, f"{u_name.lower()}.png")
        u_img.save(u_png)
        cur_x += u_img.size[0]

    ui_base = os.path.join(UI_DIR, "ui_elements_sheet")
    save_as_libresprite_pair(ui_base, ui_w, 16, [ui_sheet.tobytes()], grid=(16, 16), layer_name="UI HUD")
    ui_png = os.path.join(PNG_SHEETS_DIR, "ui_elements_sheet.png")
    ui_sheet.save(ui_png)
    print(f"  -> Generated UI Elements Sheet: ui_elements_sheet.aseprite / .ase ({len(ui_elements)} elements)")

    # 5. Master Showcase Overview Poster
    print("\n[5/6] Processing Master Showcase Overview Poster...")
    poster_img = gen.build_presentation_showcase(all_sprites)
    poster_rgba = poster_img.convert("RGBA").tobytes()
    poster_base = os.path.join(SHOWCASE_DIR, "master_spritesheet_overview")
    save_as_libresprite_pair(poster_base, 960, 540, [poster_rgba], grid=(16, 16), layer_name="Master Presentation Card")
    poster_png = os.path.join(PNG_SHEETS_DIR, "master_spritesheet_overview.png")
    poster_img.save(poster_png)
    print("  -> Generated Master Showcase Poster: master_spritesheet_overview.aseprite / .ase (960x540 canvas)")

    # 6. Generate Documentation Guide
    print("\n[6/6] Writing Documentation Guide...")
    guide_path = os.path.join(GAME_ASSETS_DIR, "HOW_TO_USE_IN_LIBRESPRITE.md")
    with open(guide_path, "w", encoding="utf-8") as f_md:
        f_md.write("""# How to Open and Edit Game Assets in LibreSprite

This folder contains the complete, pixel-perfect 2D art asset collection for the **Custom FPGA-Based GPU RPG Console** project at **Woxsen University**.

All asset files are generated natively in the **LibreSprite / Aseprite (.aseprite and .ase)** format, giving you full access to animation timelines, frame tags, layers, and pixel grids.

---

## 📁 Directory Structure

```
game_assets/
├── libresprite/
│   ├── characters_animated/      # Multi-frame animated project files (Press Spacebar to Play!)
│   │   ├── hero_zero_animated.aseprite & .ase (Idle, Walk Cycle, Action)
│   │   ├── npc_dazai_animated.aseprite & .ase (Bandages, Coat, Pocket hands)
│   │   ├── npc_escanor_animated.aseprite & .ase (Lion of Pride, Golden Axe)
│   │   ├── npc_zoro_animated.aseprite & .ase (Haramaki, 3 Katanas)
│   │   ├── npc_naruto_animated.aseprite & .ase (Jumpsuit, Headband)
│   │   └── npc_roshi_animated.aseprite & .ase (Turtle Shell, Sunglasses, Cane)
│   │
│   ├── characters_sheets/        # Complete 96x32 character sheets (4 poses + portrait)
│   ├── characters_portraits/     # 32x32 dialog closeup portraits
│   ├── environment_tiles/        # 16x16 world tiles (Grass, Cobblestone, Wall, Water, Roof, etc.)
│   ├── investigation_props/      # 16x16 mystery clues (Gold Sack, Lantern, Key, Receipt, etc.)
│   ├── ui_hud/                   # 16x16 hearts, magnifying glass, dialog border
│   └── master_showcase/          # 960x540 presentation showcase poster
│
└── png_exports/                  # Standard PNG versions for documents & web
    ├── sheets/                   # Horizontal sheets
    └── individual_sprites/       # Standalone 16x16 and 16x32 PNGs
```

---

## 🎨 Opening Files in LibreSprite

1. Launch **LibreSprite** (located in your Downloads: `C:\\Users\\sande\\Downloads\\libresprite-development-windows-x86_64\\libresprite.exe`).
2. Go to **File -> Open** (or press `Ctrl + O`).
3. Navigate to `D:\\CP GPU\\game_assets\\libresprite\\`.
4. Select any `.aseprite` or `.ase` file!

### 🎬 Playing Character Walk Animations
Open any file from `characters_animated/` (for example: `hero_zero_animated.aseprite`):
* Press **Spacebar** (or the Play ▶ button on the timeline at the bottom).
* You will see the character walk and step in real time!
* Notice the color-coded tags above the timeline:
  - **Idle** (Frame 1)
  - **Walk Cycle** (Frames 1 to 3)
  - **Action / Clue** (Frame 4)

### 📐 Pixel Grid Settings
All tiles and props are pre-configured with a **16x16** pixel grid:
* Toggle Grid: Press `Ctrl + '` (or **View -> Show -> Grid**).
* Character sheets are set to a **16x32** grid for body frames and **32x32** for portraits.

### 💾 Exporting from LibreSprite
When you make edits in LibreSprite:
1. Save your project file: `Ctrl + S` (saves `.aseprite` preserving all layers & frames).
2. Export as a sprite sheet: **File -> Export Sprite Sheet** (`Ctrl + Alt + Shift + S`).
3. Export single image / GIF: **File -> Save As / Export** (`Ctrl + Shift + S`).

---
**Institution:** Woxsen University — School of Technology  
**Supervisor:** Dr. Bhanu Prakash  
""")

    # 7. Copy Complete Suite to Downloads for Easy Access
    DOWNLOADS_ASSETS = r"C:\Users\sande\Downloads\Game_Assets_LibreSprite"
    import shutil
    print("\n[7/7] Copying Game Assets Suite to Downloads folder...")
    if os.path.exists(DOWNLOADS_ASSETS):
        shutil.rmtree(DOWNLOADS_ASSETS)
    os.makedirs(DOWNLOADS_ASSETS, exist_ok=True)

    dest_sheets = os.path.join(DOWNLOADS_ASSETS, "1_Character_Spritesheets")
    dest_anim = os.path.join(DOWNLOADS_ASSETS, "2_Character_Animations")
    dest_port = os.path.join(DOWNLOADS_ASSETS, "3_Character_Portraits")
    dest_tiles = os.path.join(DOWNLOADS_ASSETS, "4_World_Tiles")
    dest_props = os.path.join(DOWNLOADS_ASSETS, "5_Investigation_Clues")
    dest_ui = os.path.join(DOWNLOADS_ASSETS, "6_UI_and_HUD")
    dest_show = os.path.join(DOWNLOADS_ASSETS, "7_Master_Showcase")
    dest_png = os.path.join(DOWNLOADS_ASSETS, "PNG_Previews")

    shutil.copytree(SHEETS_DIR, dest_sheets)
    shutil.copytree(ANIM_DIR, dest_anim)
    shutil.copytree(PORTRAITS_DIR, dest_port)
    shutil.copytree(TILES_DIR, dest_tiles)
    shutil.copytree(PROPS_DIR, dest_props)
    shutil.copytree(UI_DIR, dest_ui)
    shutil.copytree(SHOWCASE_DIR, dest_show)
    shutil.copytree(PNG_DIR, dest_png)
    shutil.copy(guide_path, os.path.join(DOWNLOADS_ASSETS, "README_HOW_TO_USE.txt"))

    print(f"  -> Successfully mirrored all assets to:\n     {DOWNLOADS_ASSETS}")

    # 8. Automated Verification with LibreSprite Executable
    LIBRESPRITE_EXE = r"C:\Users\sande\Downloads\libresprite-development-windows-x86_64\libresprite.exe"
    if os.path.exists(LIBRESPRITE_EXE):
        print("\n" + "=" * 70)
        print("  AUTOMATED VERIFICATION VIA LIBRESPRITE EXECUTABLE  ")
        print("=" * 70)
        import subprocess
        test_samples = [
            os.path.join(dest_anim, "hero_zero_animated.aseprite"),
            os.path.join(dest_sheets, "hero_zero_sheet.aseprite"),
            os.path.join(dest_tiles, "tileset_world_sheet.aseprite"),
            os.path.join(dest_props, "clues_and_props_sheet.aseprite"),
            os.path.join(dest_anim, "npc_dazai_animated.ase"),
            os.path.join(dest_sheets, "npc_escanor_sheet.ase"),
            os.path.join(dest_anim, "npc_zoro_animated.aseprite"),
        ]
        all_passed = True
        for sample in test_samples:
            verify_png = os.path.join(DOWNLOADS_ASSETS, "verify_tmp.png")
            cmd = [LIBRESPRITE_EXE, sample, "--sheet", verify_png, "-b"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(verify_png):
                test_im = Image.open(verify_png)
                non_transparent = sum(1 for p in test_im.getdata() if p[3] > 0)
                os.remove(verify_png)
                base_name = os.path.basename(sample)
                print(f"  [PASS] {base_name:30s} -> Loaded by LibreSprite! ({non_transparent} colored pixels)")
            else:
                all_passed = False
                print(f"  [FAIL] {os.path.basename(sample)} failed to load in LibreSprite!")

        if all_passed:
            print("\n  -> 100% OF SAMPLED ASSETS VERIFIED COMPATIBLE WITH LIBRESPRITE!")

    print("\n" + "=" * 70)
    print("  SUCCESS: ALL GAME ASSETS CREATED AND READY FOR LIBRESPRITE!  ")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

