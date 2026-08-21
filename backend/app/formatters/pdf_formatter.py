import os
import re
from fpdf import FPDF
from ..parsers.docx_parser import extract_text_from_docx


class StructuredCVPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def clean_text_for_pdf(text: str) -> str:
    """Sanitize unicode characters for standard core PDF fonts."""
    if not text:
        return ""
    replacements = {
        "—": " - ",
        "–": " - ",
        "•": " * ",
        "·": " * ",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "│": "|",
        "▶": ">",
        "►": ">",
        "✔": "+",
        "★": "*",
        "✦": "*",
        "◆": "*",
        "▸": "*",
        "●": "*",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)

    # Encode to latin-1 safely replacing unsupported chars
    return text.encode("latin-1", "replace").decode("latin-1")


def convert_docx_to_pdf(docx_path: str, output_path: str) -> str:
    """Generate a clean, high-quality PDF document from the formatted DOCX."""
    try:
        raw_text = extract_text_from_docx(docx_path)
        lines = raw_text.split("\n")

        pdf = StructuredCVPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15)
        pdf.add_page()

        is_first_line = True

        for line in lines:
            cleaned = clean_text_for_pdf(line.strip())
            if not cleaned:
                pdf.ln(3)
                continue

            # Header / Name (first line)
            if is_first_line and len(cleaned) < 50:
                pdf.set_font("helvetica", "B", 18)
                pdf.set_text_color(30, 41, 59) # Slate 800
                pdf.multi_cell(0, 8, cleaned, align="L")
                pdf.ln(2)
                is_first_line = False
                continue

            is_first_line = False

            # Section Headers (ALL CAPS or known keywords)
            if cleaned.isupper() and len(cleaned) < 40:
                pdf.ln(4)
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(79, 70, 229) # Indigo 600
                pdf.cell(0, 7, cleaned, border="B", ln=1, align="L")
                pdf.ln(2)
            # Job Titles / Bold sub-headers
            elif " | " in cleaned and len(cleaned) < 80:
                pdf.set_font("helvetica", "B", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(0, 5.5, cleaned, align="L")
            # Bullet points
            elif cleaned.startswith("*") or cleaned.startswith("-"):
                pdf.set_font("helvetica", "", 9.5)
                pdf.set_text_color(71, 85, 105) # Slate 600
                pdf.multi_cell(0, 5, f"   {cleaned}", align="L")
            # Regular text
            else:
                pdf.set_font("helvetica", "", 9.5)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 5, cleaned, align="L")

        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error in convert_docx_to_pdf: {e}")
        raise Exception(f"Failed to convert to PDF: {e}")
