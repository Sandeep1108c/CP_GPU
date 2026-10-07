"""
Merge 3 project documents into a single clean PDF for presentation.
Removes all > [!NOTE], > [!WARNING], > [!IMPORTANT], > [!TIP], > [!CAUTION] blocks.
Removes emoji from headings for cleaner print output.
"""

import re
from markdown_pdf import MarkdownPdf, Section

# File paths
FILES = [
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\project_summary_verification.md",
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\nanogpt_ai_system_plan.md",
    r"C:\Users\sande\.gemini\antigravity\brain\17f0061b-0490-410b-b7fc-ce9847ede91b\artifacts\game_building_plan.md",
]

OUTPUT = r"D:\CP GPU\Custom_FPGA_GPU_Project_Document.pdf"


def clean_markdown(text):
    """Remove alert blocks, status lines, emoji, and review prompts."""
    lines = text.split('\n')
    cleaned = []
    skip_block = False

    for line in lines:
        stripped = line.strip()

        # Skip alert/admonition blocks (> [!NOTE], > [!WARNING], etc.)
        if re.match(r'>\s*\[!(NOTE|WARNING|IMPORTANT|TIP|CAUTION)\]', stripped):
            skip_block = True
            continue
        if skip_block:
            if stripped.startswith('>'):
                continue  # Still inside the block
            else:
                skip_block = False  # Block ended

        # Skip status/review lines
        if 'Status: ALL DECISIONS LOCKED IN' in stripped:
            continue
        if 'Every engineering choice has been made' in stripped:
            continue
        if 'Review this entire document' in stripped:
            continue
        if 'Review everything above' in stripped:
            continue
        if 'looks good' in stripped.lower() and 'say' in stripped.lower():
            continue
        if 'To start generating training data' in stripped:
            continue
        if stripped.startswith('> **Status'):
            continue
        if stripped.startswith('> Every engineering'):
            continue
        if stripped.startswith('> **Review'):
            continue
        if stripped.startswith('> **To start'):
            continue

        cleaned.append(line)

    result = '\n'.join(cleaned)

    # Remove emoji characters (keep text clean for print)
    result = re.sub(
        r'[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U0001FA00-\U0001FA6F'
        r'\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U0000FE0F'
        r'\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000026FF'
        r'\U0001F1E0-\U0001F1FF\U00002B50\U0000231A-\U0000231B'
        r'\U000023E9-\U000023F3\U000023F8-\U000023FA\U0001F004'
        r'\U0001F0CF\U0001F18E\U0001F191-\U0001F19A\U0001F201-\U0001F251]+',
        '', result
    )

    # Clean up resulting double-spaces in headings
    result = re.sub(r'#\s+\s+', '# ', result)
    result = re.sub(r'##\s+\s+', '## ', result)
    result = re.sub(r'###\s+\s+', '### ', result)

    # Remove multiple consecutive blank lines
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    return result


def main():
    print("=" * 60)
    print("  Custom FPGA GPU — PDF Document Generator")
    print("=" * 60)

    # Title page content
    title_page = """# Design & Implementation of a Custom FPGA-Based Graphics Processing Unit (GPU)

## "Find the Thief" — 2D Mystery Game with AI-Driven NPC Dialogue

---

**Team Members:**
- Tutika Sandeep
- Ayush
- Namburi Venkata Yeshwanth
- Ghaffar Salman
- Faisal Mohammed

**Supervisor:** Dr. Bhanu Prakash

**Institution:** School of Technology, Woxsen University

---

**Hardware Platform:**
- ESP32-S3-DevKitC-1 (Host CPU + AI Brain)
- Sipeed Tang Nano 20K (FPGA Graphics Engine)
- Cosmic Byte Blitz Gamepad (Player Input)
- HDMI Output at 640x480 @ 60Hz

---

"""

    # Read and clean all files
    sections_text = [title_page]
    section_names = [
        "Part 1: Project Specification",
        "Part 2: nanoGPT AI System",
        "Part 3: Game Development Plan"
    ]

    for i, filepath in enumerate(FILES):
        print(f"Reading: {section_names[i]}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Clean the content
        content = clean_markdown(content)

        # Add part separator
        separator = f"\n\n---\n\n# {section_names[i]}\n\n---\n\n"
        sections_text.append(separator + content)

    # Combine all content
    full_content = '\n'.join(sections_text)

    print(f"\nGenerating PDF...")

    # Create PDF
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(full_content))
    pdf.meta["title"] = "Custom FPGA GPU — Project Document"
    pdf.meta["author"] = "Tutika Sandeep et al."
    pdf.save(OUTPUT)

    print(f"\nPDF saved to: {OUTPUT}")
    print(f"Done! You can now print this file.")


if __name__ == '__main__':
    main()
