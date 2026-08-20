import docx
import re

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {e}")

def extract_placeholders_from_docx(file_path: str) -> list[str]:
    text = extract_text_from_docx(file_path)
    # Match patterns like {{name}}, {{ skill1 }}
    placeholders = re.findall(r'\{\{[^}]+\}\}', text)
    return list(set(placeholders))
