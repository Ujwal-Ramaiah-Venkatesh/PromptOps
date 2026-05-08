from docx import Document

# Read the .docx file
doc = Document('PromptOps_Development_Blueprint.docx')

# Extract text
full_text = []
for para in doc.paragraphs:
    full_text.append(para.text)

# Save to text file
with open('PromptOps_Development_Blueprint.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(full_text))

print("Conversion complete! Output saved to PromptOps_Development_Blueprint.txt")
