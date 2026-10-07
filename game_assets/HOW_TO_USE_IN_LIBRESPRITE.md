# How to Open and Edit Game Assets in LibreSprite

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

1. Launch **LibreSprite** (located in your Downloads: `C:\Users\sande\Downloads\libresprite-development-windows-x86_64\libresprite.exe`).
2. Go to **File -> Open** (or press `Ctrl + O`).
3. Navigate to `D:\CP GPU\game_assets\libresprite\`.
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
