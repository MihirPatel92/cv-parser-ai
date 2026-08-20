import subprocess
import os
from fpdf import FPDF
from ..parsers.docx_parser import extract_text_from_docx

def convert_docx_to_pdf(docx_path: str, output_path: str) -> str:
    # Method 1: LibreOffice headless
    try:
        output_dir = os.path.dirname(output_path)
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            docx_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # libreoffice names the file same as docx but .pdf
        base_name = os.path.splitext(os.path.basename(docx_path))[0]
        lo_output_path = os.path.join(output_dir, f"{base_name}.pdf")
        if os.path.exists(lo_output_path):
            if lo_output_path != output_path:
                os.rename(lo_output_path, output_path)
            return output_path
    except Exception as e:
        print(f"LibreOffice conversion failed: {e}. Falling back to fpdf2.")
        
    # Method 2: Fallback to fpdf2
    try:
        text = extract_text_from_docx(docx_path)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'))
            
        pdf.output(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert to PDF: {e}")
