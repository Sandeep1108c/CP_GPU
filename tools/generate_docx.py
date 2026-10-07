"""
Merge 3 project documents into a single Word (.docx) for editing.
Removes alert blocks. Preserves tables, code blocks, and headings.
"""

import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

FILES = [
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\project_summary_verification.md",
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\nanogpt_ai_system_plan.md",
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\game_building_plan.md",
]
OUTPUT = r"D:\CP GPU\Custom_FPGA_GPU_Project_Document.docx"

SECTION_NAMES = [
    "Part 1: Project Specification",
    "Part 2: nanoGPT AI System",
    "Part 3: Game Development Plan"
]

# Emoji removal pattern
EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U0001FA00-\U0001FAFF'
    r'\U00002702-\U000027B0\U0000FE0F\U0001F600-\U0001F64F'
    r'\U0001F680-\U0001F6FF\U00002600-\U000026FF\U0001F1E0-\U0001F1FF'
    r'\U00002B50\U0000231A-\U0000231B\U000023E9-\U000023FA'
    r'\U0001F004\U0001F0CF\U0001F18E\U0001F191-\U0001F19A'
    r'\U0001F201-\U0001F251]+'
)


def strip_emoji(text):
    return EMOJI_RE.sub('', text).strip()


def clean_lines(text):
    """Remove alert blocks and status/review lines."""
    lines = text.split('\n')
    cleaned = []
    skip = False
    for line in lines:
        s = line.strip()
        if re.match(r'>\s*\[!(NOTE|WARNING|IMPORTANT|TIP|CAUTION)\]', s):
            skip = True
            continue
        if skip:
            if s.startswith('>'):
                continue
            skip = False
        if any(x in s for x in [
            'Status: ALL DECISIONS LOCKED IN',
            'Every engineering choice has been made',
            'Review this entire document',
            'To start generating training data',
        ]):
            continue
        if s.startswith('> **Status') or s.startswith('> Every engineering'):
            continue
        if s.startswith('> **Review') or s.startswith('> **To start'):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def set_cell_text(cell, text, bold=False, size=9):
    cell.text = ''
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.name = 'Calibri'
    run.bold = bold


def add_table(doc, header_row, data_rows):
    """Add a formatted table to the document."""
    cols = len(header_row)
    table = doc.add_table(rows=1 + len(data_rows), cols=cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header
    for i, h in enumerate(header_row):
        set_cell_text(table.rows[0].cells[i], h.strip(), bold=True, size=9)
        shading = table.rows[0].cells[i]._element
        from docx.oxml.ns import qn
        from lxml import etree
        tc_pr = shading.get_or_add_tcPr()
        shd = etree.SubElement(tc_pr, qn('w:shd'))
        shd.set(qn('w:fill'), '2B579A')
        shd.set(qn('w:val'), 'clear')
        # White text for header
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Data rows
    for r_idx, row_data in enumerate(data_rows):
        for c_idx, val in enumerate(row_data):
            if c_idx < cols:
                set_cell_text(table.rows[r_idx + 1].cells[c_idx], val.strip(), size=9)

    doc.add_paragraph('')  # spacer


def parse_table(lines, start_idx):
    """Parse a markdown table starting at start_idx, return (header, rows, end_idx)."""
    header_line = lines[start_idx]
    cols = [c.strip() for c in header_line.strip('|').split('|')]

    # Skip separator line (|---|---|)
    sep_idx = start_idx + 1

    rows = []
    idx = sep_idx + 1
    while idx < len(lines) and '|' in lines[idx] and lines[idx].strip().startswith('|'):
        row = [c.strip() for c in lines[idx].strip('|').split('|')]
        rows.append(row)
        idx += 1

    return cols, rows, idx


def process_markdown(doc, text):
    """Convert cleaned markdown text into Word document elements."""
    lines = text.split('\n')
    i = 0
    in_code = False
    code_block = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code block toggle
        if stripped.startswith('```'):
            if in_code:
                # End code block — add as formatted paragraph
                code_text = '\n'.join(code_block)
                p = doc.add_paragraph()
                p.style = doc.styles['Normal']
                run = p.add_run(code_text)
                run.font.name = 'Consolas'
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(30, 30, 30)
                p.paragraph_format.left_indent = Inches(0.3)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                code_block = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_block.append(line)
            i += 1
            continue

        # Skip mermaid blocks
        if stripped.startswith('```mermaid'):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1
            i += 1
            continue

        # Horizontal rule
        if stripped == '---' or stripped == '***':
            # doc.add_page_break()
            p = doc.add_paragraph('―' * 60)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.color.rgb = RGBColor(180, 180, 180)
            run.font.size = Pt(8)
            i += 1
            continue

        # Tables
        if '|' in stripped and stripped.startswith('|') and i + 1 < len(lines):
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if re.match(r'\|[\s\-:|]+\|', next_line):
                header, rows, end_idx = parse_table(lines, i)
                add_table(doc, header, rows)
                i = end_idx
                continue

        # Headings
        if stripped.startswith('#'):
            match = re.match(r'^(#{1,4})\s+(.*)', stripped)
            if match:
                level = len(match.group(1))
                text_content = strip_emoji(match.group(2))
                # Remove ** bold markers from headings
                text_content = text_content.replace('**', '')
                heading_style = f'Heading {level}'
                doc.add_heading(text_content, level=level)
                i += 1
                continue

        # Blockquotes (non-alert ones that survived cleaning)
        if stripped.startswith('>'):
            quote_text = stripped.lstrip('> ').strip()
            if quote_text:
                quote_text = strip_emoji(quote_text).replace('**', '')
                p = doc.add_paragraph(quote_text)
                p.paragraph_format.left_indent = Inches(0.4)
                p.runs[0].font.italic = True if p.runs else None
            i += 1
            continue

        # Bullet points
        if re.match(r'^[\-\*]\s+', stripped):
            bullet_text = re.sub(r'^[\-\*]\s+', '', stripped)
            bullet_text = strip_emoji(bullet_text)
            # Handle bold within bullets
            p = doc.add_paragraph(style='List Bullet')
            parts = re.split(r'\*\*(.*?)\*\*', bullet_text)
            for j, part in enumerate(parts):
                run = p.add_run(part)
                run.font.size = Pt(10)
                run.font.name = 'Calibri'
                if j % 2 == 1:  # Bold parts
                    run.bold = True
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s+', stripped):
            item_text = re.sub(r'^\d+\.\s+', '', stripped)
            item_text = strip_emoji(item_text)
            p = doc.add_paragraph(style='List Number')
            parts = re.split(r'\*\*(.*?)\*\*', item_text)
            for j, part in enumerate(parts):
                run = p.add_run(part)
                run.font.size = Pt(10)
                run.font.name = 'Calibri'
                if j % 2 == 1:
                    run.bold = True
            i += 1
            continue

        # Empty lines
        if not stripped:
            i += 1
            continue

        # Normal paragraph
        clean_text = strip_emoji(stripped)
        if clean_text:
            p = doc.add_paragraph()
            # Handle inline bold
            parts = re.split(r'\*\*(.*?)\*\*', clean_text)
            for j, part in enumerate(parts):
                # Handle inline code
                code_parts = re.split(r'`([^`]+)`', part)
                for k, cp in enumerate(code_parts):
                    run = p.add_run(cp)
                    run.font.size = Pt(10)
                    run.font.name = 'Calibri'
                    if j % 2 == 1:
                        run.bold = True
                    if k % 2 == 1:
                        run.font.name = 'Consolas'
                        run.font.size = Pt(9)

        i += 1


def main():
    print("=" * 50)
    print("  Generating Word Document (.docx)")
    print("=" * 50)

    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(10)

    # ---- TITLE PAGE ----
    doc.add_paragraph('')
    doc.add_paragraph('')
    doc.add_paragraph('')

    title = doc.add_heading('Design & Implementation of a Custom FPGA-Based Graphics Processing Unit (GPU)', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_heading('"Find the Thief" — 2D Mystery Game with AI-Driven NPC Dialogue', level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph('')

    info_lines = [
        ('Team Members:', 'Tutika Sandeep, Ayush, Namburi Venkata Yeshwanth, Ghaffar Salman, Faisal Mohammed'),
        ('Supervisor:', 'Dr. Bhanu Prakash'),
        ('Institution:', 'School of Technology, Woxsen University'),
        ('', ''),
        ('Hardware:', 'ESP32-S3-DevKitC-1 + Sipeed Tang Nano 20K'),
        ('Display:', 'HDMI 640x480 @ 60Hz'),
        ('Input:', 'Cosmic Byte Blitz Gamepad (USB)'),
        ('AI Engine:', 'nanoGPT ~4.8M parameters (INT8 on ESP32-S3)'),
    ]
    for label, value in info_lines:
        if not label:
            doc.add_paragraph('')
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_label = p.add_run(label + ' ')
        run_label.bold = True
        run_label.font.size = Pt(11)
        run_val = p.add_run(value)
        run_val.font.size = Pt(11)

    doc.add_page_break()

    # ---- PROCESS EACH SECTION ----
    for idx, filepath in enumerate(FILES):
        print(f"Processing: {SECTION_NAMES[idx]}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        content = clean_lines(content)

        # Add section header
        doc.add_heading(SECTION_NAMES[idx], level=1)

        # Process markdown into document
        process_markdown(doc, content)

        # Page break between sections
        if idx < len(FILES) - 1:
            doc.add_page_break()

    # Save
    doc.save(OUTPUT)
    print(f"\nSaved: {OUTPUT}")
    print("Done! Open it in Word to make your edits.")


if __name__ == '__main__':
    main()
