#!/usr/bin/env python3
"""
Build Professional Word Document (.docx) for Final Presentation Project Report.
Custom FPGA-Based GPU & Edge AI Engine — Woxsen University

Applies:
- Academic & Executive styling (Navy #1B365D, Slate #4A607A, Gold #D4AF37)
- Formatted Title block with University & Team credentials
- Styled Headings (Heading 1, 2, 3) with accent colors and clean spacing
- Clean data tables with shaded navy headers, white text, and light gridlines
- Code / Verilog / C blocks in light gray shading with Consolas monospace
- Technical Callout boxes with thick left accent borders
- Embedded High-Resolution Graphics:
  * Hero Cast Artwork (Retro 16-bit RPG Showcase)
  * System Architecture Schematic (FPGA + ESP32 Console)
  * Master Asset Presentation Overview Poster (All Sprites, Tiles, Clues, UI)
"""

import os
import re
import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
RAW_DIR = os.path.join(ASSETS_DIR, "raw")

MD_REPORT_PATH = os.path.join(DOCS_DIR, "Final_Presentation_Project_Report.md")
DOCX_OUTPUT_PATH = os.path.join(DOCS_DIR, "Final_Presentation_Project_Report.docx")

# Color Palette Constants
COLOR_NAVY = RGBColor(27, 54, 93)       # #1B365D - Primary Header
COLOR_SLATE = RGBColor(74, 96, 122)     # #4A607A - Secondary Header
COLOR_GOLD = RGBColor(212, 175, 55)     # #D4AF37 - Accents & Rules
COLOR_DARK = RGBColor(40, 44, 52)       # #282C34 - Body text
COLOR_MUTED = RGBColor(100, 110, 125)   # #646E7D - Captions & Subtitles
COLOR_GREEN = RGBColor(34, 139, 34)     # #228B22 - Success / Pass

def set_cell_background(cell, hex_color):
    """Sets cell background shading."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}" w:val="clear"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets inner cell padding in twips."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_callout_box(doc, text_paragraphs, border_hex="1B365D", bg_hex="F0F4F8", title=None):
    """Adds a stylish callout box with a colored left accent border."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    cell = table.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=150)

    # Set left border thick, clear others
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_hex}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15

    if title:
        run_title = p.add_run(f"★ {title}\n")
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(10.5)
        run_title.font.bold = True
        run_title.font.color.rgb = COLOR_NAVY

    for idx, tp in enumerate(text_paragraphs):
        if idx > 0 or title:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15

        run = p.add_run(tp)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text):
    """Adds a formatted code snippet block with light gray shading."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    cell = table.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, "F4F5F7")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=120)

    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="D0D5DD"/>'
        f'<w:left w:val="single" w:sz="18" w:space="0" w:color="1B365D"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="D0D5DD"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="D0D5DD"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05

    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def format_table(table, col_widths=None):
    """Styles tables with navy header, white bold text, and alternating rows."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Style Header Row
    for idx, cell in enumerate(table.rows[0].cells):
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Style Data Rows
    for r_idx, row in enumerate(table.rows[1:], start=1):
        bg = "FFFFFF" if r_idx % 2 == 1 else "F8FAFC"
        for c_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9.0)
                run.font.color.rgb = COLOR_DARK
                if "PASS" in run.text or "100%" in run.text:
                    run.font.bold = True
                    run.font.color.rgb = COLOR_GREEN

    # Apply column widths if specified
    if col_widths:
        for row in table.rows:
            for c_idx, width in enumerate(col_widths):
                if c_idx < len(row.cells):
                    row.cells[c_idx].width = width

def add_figure(doc, img_path, caption_text, width=Inches(6.2)):
    """Embeds an image centered with a styled caption."""
    if not os.path.exists(img_path):
        print(f"Warning: Image not found at {img_path}")
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(2)
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=width)

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(f"Figure: {caption_text}")
    run_cap.font.name = "Calibri"
    run_cap.font.size = Pt(8.5)
    run_cap.font.italic = True
    run_cap.font.color.rgb = COLOR_MUTED

def parse_markdown_to_docx(md_path, docx_path):
    print(f"Reading markdown report from: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = Document()

    # Configure Margins: 1 inch on all sides
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    # ---------------------------------------------------------
    # COVER / HEADER BLOCK
    # ---------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_top.paragraph_format.space_after = Pt(2)
    run_uni = p_top.add_run("WOXSEN UNIVERSITY — SCHOOL OF TECHNOLOGY")
    run_uni.font.name = "Calibri"
    run_uni.font.size = Pt(11)
    run_uni.font.bold = True
    run_uni.font.color.rgb = COLOR_SLATE

    p_sub_inst = doc.add_paragraph()
    p_sub_inst.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sub_inst.paragraph_format.space_after = Pt(8)
    run_sub = p_sub_inst.add_run("Department of Computer Science & Engineering | Capstone Engineering Defense")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(9.5)
    run_sub.font.color.rgb = COLOR_MUTED

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("Design & Implementation of a Custom FPGA-Based Graphics Processing Unit (GPU) & Edge AI Engine")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_NAVY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sub.paragraph_format.space_after = Pt(10)
    run_sub = p_sub.add_run('"Find the Thief" Retro RPG Console — Comprehensive Final Presentation & Engineering Milestone Report')
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(12)
    run_sub.font.bold = True
    run_sub.font.color.rgb = COLOR_SLATE

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Supervisor", "Dr. Bhanu Prakash"),
        ("Core Engineering Team", "Tutika Sandeep (Project Lead), Ayush, Namburi Venkata Yeshwanth, Ghaffar Salman, Faisal Mohammed"),
        ("Hardware Platforms", "Sipeed Tang Nano 20K (Gowin GW2AR-LV18QN88C8/I7) + ESP32-S3-DevKitC-1"),
        ("Target Display & AI", "HDMI 640x480 @ 60 Hz (TMDS Differential) | On-Device INT8 nanoGPT (~4.79M Params)")
    ]
    for idx, (label, val) in enumerate(meta_data):
        r = meta_table.rows[idx]
        set_cell_background(r.cells[0], "F1F5F9")
        set_cell_background(r.cells[1], "FFFFFF")
        set_cell_margins(r.cells[0], top=40, bottom=40, left=80, right=80)
        set_cell_margins(r.cells[1], top=40, bottom=40, left=80, right=80)
        r.cells[0].width = Inches(1.8)
        r.cells[1].width = Inches(4.7)

        p0 = r.cells[0].paragraphs[0]
        run0 = p0.add_run(label)
        run0.font.name = "Calibri"
        run0.font.size = Pt(8.5)
        run0.font.bold = True
        run0.font.color.rgb = COLOR_NAVY

        p1 = r.cells[1].paragraphs[0]
        run1 = p1.add_run(val)
        run1.font.name = "Calibri"
        run1.font.size = Pt(8.5)
        run1.font.color.rgb = COLOR_DARK

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(8)
    p_div.paragraph_format.space_after = Pt(8)

    # Embed Hero Graphics Early in Document
    hero_cast_img = os.path.join(ASSETS_DIR, "presentation_cast_hero.jpg")
    if os.path.exists(hero_cast_img):
        add_figure(doc, hero_cast_img, "The 'Find the Thief' Cast & Retro Video Game Visual Identity: Detective Zero, Dazai, Escanor, Zoro, Naruto, and Roshi.", width=Inches(6.2))

    # ---------------------------------------------------------
    # PARSE SECTIONS AND CONTENT
    # ---------------------------------------------------------
    lines = md_text.split("\n")
    idx = 0
    in_code = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table(tbl_lines):
        if not tbl_lines:
            return
        # Parse rows
        parsed_rows = []
        for l in tbl_lines:
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', l):
                continue # Skip markdown alignment row
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            parsed_rows.append(cells)

        if not parsed_rows:
            return

        header = parsed_rows[0]
        data = parsed_rows[1:]
        cols = len(header)
        table = doc.add_table(rows=1 + len(data), cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Fill Header
        for c_idx, h_text in enumerate(header):
            cell = table.rows[0].cells[c_idx]
            cell.text = h_text

        # Fill Data
        for r_idx, row_vals in enumerate(data):
            for c_idx in range(cols):
                val = row_vals[c_idx] if c_idx < len(row_vals) else ""
                cell = table.rows[r_idx + 1].cells[c_idx]
                cell.text = val

        format_table(table)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Code block handler
        if stripped.startswith("```"):
            if in_code:
                # Flush code block
                add_code_block(doc, "\n".join(code_lines))
                code_lines = []
                in_code = False
            else:
                in_code = True
                code_lines = []
            idx += 1
            continue

        if in_code:
            code_lines.append(line)
            idx += 1
            continue

        # Table handler
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
                table_lines = [stripped]
            else:
                table_lines.append(stripped)
            idx += 1
            continue
        else:
            if in_table:
                flush_table(table_lines)
                table_lines = []
                in_table = False

        # Headings
        if stripped.startswith("# "):
            # Heading 1 already formatted in cover block, treat subsequent as Major Header
            h_text = stripped[2:].strip()
            p = doc.add_heading(h_text, level=1)
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(15)
                r.font.bold = True
                r.font.color.rgb = COLOR_NAVY
            idx += 1
            continue

        if stripped.startswith("## "):
            h_text = stripped[3:].strip()
            p = doc.add_heading(h_text, level=2)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(13)
                r.font.bold = True
                r.font.color.rgb = COLOR_NAVY

            # Contextual Image Injections
            if "System Architecture" in h_text:
                hw_img = os.path.join(ASSETS_DIR, "presentation_hardware_console.jpg")
                if os.path.exists(hw_img):
                    add_figure(doc, hw_img, "System Architecture: Gowin GW2AR-18C Tang Nano 20K FPGA Custom GPU Interfaced to ESP32-S3 Host with 60 FPS HDMI Output.", width=Inches(6.2))

            if "Visual Assets" in h_text or "Spritesheet Pipeline" in h_text:
                overview_img = os.path.join(RAW_DIR, "master_spritesheet_overview.png")
                if os.path.exists(overview_img):
                    add_figure(doc, overview_img, "Master 2D Asset Architecture: Cast Spritesheets, 16x16 World Tileset, Clues & Props, and UI HUD Elements.", width=Inches(6.2))

            idx += 1
            continue

        if stripped.startswith("### "):
            h_text = stripped[4:].strip()
            p = doc.add_heading(h_text, level=3)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(11)
                r.font.bold = True
                r.font.color.rgb = COLOR_SLATE
            idx += 1
            continue

        # Callout Detection (Alert block or Key Engineering Accomplishments)
        if "Critical SDRAM Bottleneck" in stripped or "Engineering Accomplishments" in stripped:
            # Gather bullet points or text
            callout_title = stripped.replace("*", "").replace("#", "").strip()
            callout_paras = []
            idx += 1
            while idx < len(lines) and lines[idx].strip() and not lines[idx].strip().startswith("#"):
                l_text = lines[idx].strip()
                if l_text.startswith("- ") or l_text.startswith("1.") or l_text.startswith("2.") or l_text.startswith("3."):
                    callout_paras.append(l_text)
                else:
                    callout_paras.append(l_text)
                idx += 1
            add_callout_box(doc, callout_paras, border_hex="1B365D", bg_hex="F0F4F8", title=callout_title)
            continue

        # Standard Paragraph / Bullets
        if stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15

            # Handle bullet points
            if stripped.startswith("- ") or stripped.startswith("* "):
                p.paragraph_format.left_indent = Inches(0.25)
                stripped = "•  " + stripped[2:]

            # Inline bold / math parser
            # Replace basic markdown formatting
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', stripped)
            for part in parts:
                if not part:
                    continue
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                elif part.startswith("*") and part.endswith("*"):
                    run = p.add_run(part[1:-1])
                    run.font.italic = True
                elif part.startswith("`") and part.endswith("`"):
                    run = p.add_run(part[1:-1])
                    run.font.name = "Consolas"
                    run.font.size = Pt(9.0)
                    run.font.color.rgb = COLOR_NAVY
                else:
                    run = p.add_run(part)

                run.font.name = "Calibri"
                run.font.size = Pt(10)
                run.font.color.rgb = COLOR_DARK

        idx += 1

    # Final cleanup if table still open
    if in_table:
        flush_table(table_lines)

    # Save Document
    doc.save(docx_path)
    print(f"\n[SUCCESS] Word document generated successfully: {docx_path}")
    print(f"File size: {os.path.getsize(docx_path):,} bytes")

if __name__ == "__main__":
    parse_markdown_to_docx(MD_REPORT_PATH, DOCX_OUTPUT_PATH)
