from docx import Document
from docx.shared import Pt, Inches

# Create a new document
doc = Document()

# Add main title
doc.add_heading('PromptOps Development Blueprint', 0)
doc.add_heading('Complete Phases 1-5 Including MLOps Extension', 1)

print("Reading original blueprint...")
# Read the original text content
with open('PromptOps_Development_Blueprint.txt', 'r', encoding='utf-8') as f:
    original_content = f.read()

# Add the original content (Phases 1-4)
doc.add_heading('Phases 1-4: Core DevOps Platform', 1)
for line in original_content.split('\n')[:260]:  # Up to Phase 5
    if line.strip():
        if line.startswith('Phase'):
            doc.add_heading(line, level=1)
        elif line.startswith('Week'):
            doc.add_heading(line, level=2)
        else:
            doc.add_paragraph(line)

print("Reading MLOps extension...")
# Read the detailed MLOps content
with open('PromptOps_MLOps_Extension.md', 'r', encoding='utf-8') as f:
    mlops_content = f.read()

# Add Phase 5 MLOps Extension
doc.add_page_break()
doc.add_heading('Phase 5: MLOps Agent — ML Lifecycle Automation (Detailed)', 1)

# Add MLOps content line by line
in_code_block = False
for line in mlops_content.split('\n'):
    # Skip initial markdown metadata
    if line.startswith('# PromptOps MLOps Extension'):
        continue
    if line.startswith('##'):
        continue

    if line.startswith('```'):
        in_code_block = not in_code_block
        continue

    if in_code_block:
        p = doc.add_paragraph(line)
        p.style = 'No Spacing'
        continue

    if line.startswith('### '):
        doc.add_heading(line[4:], level=2)
    elif line.startswith('## '):
        doc.add_heading(line[3:], level=1)
    elif line.startswith('# '):
        doc.add_heading(line[2:], level=1)
    elif line.strip():
        doc.add_paragraph(line)

# Save the complete document
output_file = 'PromptOps_Complete_Blueprint_with_MLOps.docx'
doc.save(output_file)
print(f"\n✅ Complete blueprint created successfully!")
print(f"📄 File: {output_file}")
print(f"📊 Contains: Phases 1-5 (DevOps + MLOps)")
