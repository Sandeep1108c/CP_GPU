#!/usr/bin/env python3
"""
Replace ugly ASCII architecture art in Final_Presentation_Project_Report.odt
with the high-resolution publication-quality system architecture diagram image.
"""

import os
import zipfile
import re

ODT_PATH = r"C:\Users\sande\Downloads\Final_Presentation_Project_Report.odt"
BACKUP_PATH = r"C:\Users\sande\Downloads\Final_Presentation_Project_Report_backup.odt"
OUTPUT_ODT = r"C:\Users\sande\Downloads\Final_Presentation_Project_Report.odt"
DOCS_ODT = r"D:\CP GPU\docs\Final_Presentation_Project_Report.odt"
DOCS_DOCX = r"D:\CP GPU\docs\Final_Presentation_Project_Report.docx"
DIAGRAM_PNG = r"D:\CP GPU\docs\system_architecture_diagram.png"

def patch_odt():
    if not os.path.exists(ODT_PATH):
        print(f"Error: {ODT_PATH} not found!")
        return

    # 1. Backup original
    if not os.path.exists(BACKUP_PATH):
        with open(ODT_PATH, "rb") as f_src, open(BACKUP_PATH, "wb") as f_dst:
            f_dst.write(f_src.read())
        print(f"Created backup: {BACKUP_PATH}")

    # Read diagram image bytes
    with open(DIAGRAM_PNG, "rb") as f_img:
        img_bytes = f_img.read()
    img_name = "Pictures/system_architecture_diagram.png"

    # Read all files from ODT ZIP
    files_dict = {}
    with zipfile.ZipFile(ODT_PATH, "r") as z_in:
        for info in z_in.infolist():
            files_dict[info.filename] = z_in.read(info.filename)

    # 2. Add image file to Pictures/
    files_dict[img_name] = img_bytes
    print(f"Added {img_name} ({len(img_bytes):,} bytes)")

    # 3. Update META-INF/manifest.xml
    manifest_xml = files_dict.get("META-INF/manifest.xml", b"").decode("utf-8")
    entry_tag = '<manifest:file-entry manifest:full-path="Pictures/system_architecture_diagram.png" manifest:media-type="image/png"/>'
    if entry_tag not in manifest_xml:
        manifest_xml = manifest_xml.replace(
            "</manifest:manifest>",
            f"  {entry_tag}\n</manifest:manifest>"
        )
        files_dict["META-INF/manifest.xml"] = manifest_xml.encode("utf-8")
        print("Updated META-INF/manifest.xml with new image entry")

    # 4. Update content.xml: Replace Table2 (the ASCII diagram) with draw:frame
    content_xml = files_dict["content.xml"].decode("utf-8")

    # Locate Table2
    t_start = content_xml.find('<table:table table:name="Table2"')
    if t_start == -1:
        print("Could not find '<table:table table:name=\"Table2\"' in content.xml!")
        return

    t_end = content_xml.find("</table:table>", t_start)
    if t_end == -1:
        print("Could not find end of Table2!")
        return
    t_end += len("</table:table>")

    table2_chunk = content_xml[t_start:t_end]
    print(f"Found Table2: {len(table2_chunk):,} characters")

    # Create new draw:frame element
    # Width: 16.5 cm, Height: 9.6 cm (proportional to 2200x1280)
    frame_replacement = (
        '<text:p text:style-name="P_Center" text:class="figure">'
        '<draw:frame draw:style-name="fr1" draw:name="Figure 2.1 System Architecture" text:anchor-type="as-char" svg:width="16.500cm" svg:height="9.600cm" draw:z-index="3">'
        '<draw:image xlink:href="Pictures/system_architecture_diagram.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad" draw:mime-type="image/png"/>'
        '</draw:frame>'
        '</text:p>'
        '<text:p text:style-name="P_Caption">'
        '<text:span text:style-name="T_Bold">Figure 2.1: </text:span>'
        'End-to-End System Hardware &amp; Software Architecture — ESP32-S3 Host Controller to Gowin GW2AR-18C FPGA Custom GPU Pipeline.'
        '</text:p>'
    )

    new_content_xml = content_xml[:t_start] + frame_replacement + content_xml[t_end:]
    files_dict["content.xml"] = new_content_xml.encode("utf-8")
    print("Replaced ASCII Table2 with high-res Figure 2.1 draw:frame in content.xml")

    # 5. Write back to ODT
    with zipfile.ZipFile(OUTPUT_ODT, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
        for fname, data in files_dict.items():
            z_out.writestr(fname, data)
    print(f"Successfully saved updated ODT to {OUTPUT_ODT}")

    # Also save a copy to project docs/
    with zipfile.ZipFile(DOCS_ODT, "w", compression=zipfile.ZIP_DEFLATED) as z_docs:
        for fname, data in files_dict.items():
            z_docs.writestr(fname, data)
    print(f"Saved copy to {DOCS_ODT}")

if __name__ == "__main__":
    patch_odt()
