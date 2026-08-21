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
        self.set_text_color(160, 160, 160)
        self.cell(self.epw, 8, f"Page {self.page_no()}", align="C")


def sanitize_text(text: str) -> str:
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
        "\t": "    ",
        "\r": "",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)

    # Encode to latin-1 safely replacing unsupported chars
    return text.encode("latin-1", "replace").decode("latin-1")


def convert_docx_to_pdf(docx_path: str, output_path: str) -> str:
    """Generate a clean, high-quality, valid PDF document from the formatted DOCX."""
    raw_text = extract_text_from_docx(docx_path)
    lines = [line.strip() for line in raw_text.split("\n")]

    pdf = StructuredCVPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    epw = pdf.epw # Effective page width (width minus left and right margins)
    is_first_line = True

    for line in lines:
        cleaned = sanitize_text(line)
        if not cleaned:
            pdf.ln(2)
            continue

        # Always reset x to left margin before printing each block
        pdf.set_x(pdf.l_margin)

        # Candidate Name (Header)
        if is_first_line and len(cleaned) < 60:
            pdf.set_font("helvetica", "B", 16)
            pdf.set_text_color(30, 41, 59) # Slate 800
            pdf.multi_cell(epw, 7, cleaned, align="L")
            pdf.ln(1)
            is_first_line = False
            continue

        is_first_line = False

        # Section Headers (ALL CAPS or known keywords)
        if (cleaned.isupper() and len(cleaned) < 50) or cleaned in (
            "PROFESSIONAL SUMMARY",
            "TECHNICAL SKILLS",
            "PROFESSIONAL EXPERIENCE",
            "EXPERIENCE",
            "EDUCATION",
            "CERTIFICATIONS",
            "KEY PROJECTS",
            "PROJECTS",
            "CORE COMPETENCIES",
        ):
            pdf.ln(3)
            pdf.set_font("helvetica", "B", 10.5)
            pdf.set_text_color(79, 70, 229) # Indigo 600
            pdf.multi_cell(epw, 6, cleaned, border="B", align="L")
            pdf.ln(2)
        # Job Titles / Subheadings
        elif " | " in cleaned and len(cleaned) < 100:
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(epw, 5, cleaned, align="L")
        # Bullet points
        elif cleaned.startswith("*") or cleaned.startswith("-"):
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(71, 85, 105) # Slate 600
            bullet_content = cleaned.lstrip("*- ")
            pdf.multi_cell(epw, 4.5, f"  *  {bullet_content}", align="L")
        # Regular text / paragraphs
        else:
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(epw, 4.5, cleaned, align="L")

    # Ensure parent output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf.output(output_path)
    return output_path
