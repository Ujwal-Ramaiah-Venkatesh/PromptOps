from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Read the existing document
doc = Document('PromptOps_Development_Blueprint.docx')

# Read the MLOps extension markdown
with open('PromptOps_MLOps_Extension.md', 'r', encoding='utf-8') as f:
    mlops_content = f.read()

# Add a page break
doc.add_page_break()

# Add Phase 5 heading
heading = doc.add_heading('Phase 5: MLOps Agent — ML Lifecycle Automation', level=1)

# Parse and add the MLOps content
lines = mlops_content.split('\n')
skip_until_line = 0

for i, line in enumerate(lines):
    if i < skip_until_line:
        continue

    # Skip the markdown title and initial headers until Executive Summary
    if i < 10:
        continue

    if line.startswith('# '):
        doc.add_heading(line[2:], level=1)
    elif line.startswith('## '):
        doc.add_heading(line[3:], level=2)
    elif line.startswith('### '):
        doc.add_heading(line[4:], level=3)
    elif line.startswith('#### '):
        doc.add_heading(line[5:], level=4)
    elif line.startswith('```'):
        # Handle code blocks
        code_lines = []
        for j in range(i+1, len(lines)):
            if lines[j].startswith('```'):
                skip_until_line = j + 1
                break
            code_lines.append(lines[j])
        if code_lines:
            p = doc.add_paragraph('\n'.join(code_lines))
            p.style = 'Intense Quote'
    elif line.startswith('| '):
        # Skip table lines for now - just add as text
        doc.add_paragraph(line)
    elif line.startswith('**') and line.endswith('**'):
        # Bold text
        p = doc.add_paragraph()
        run = p.add_run(line.strip('*'))
        run.bold = True
    elif line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('*'):
        # Bullet point
        p = doc.add_paragraph(line.strip().lstrip('-•* '))
        p.style = 'List Paragraph'
    elif line.strip().startswith('✅'):
        # Checklist item
        p = doc.add_paragraph(line)
        p.style = 'List Paragraph'
    elif line.strip() == '---':
        # Horizontal rule - add spacing
        doc.add_paragraph()
    elif line.strip():
        # Regular paragraph
        doc.add_paragraph(line)

# Save the updated document
doc.save('PromptOps_Development_Blueprint_with_MLOps.docx')
print("✅ MLOps content merged successfully!")
print("New file: PromptOps_Development_Blueprint_with_MLOps.docx")
