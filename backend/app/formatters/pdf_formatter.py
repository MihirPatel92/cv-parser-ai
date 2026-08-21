import os
import re
from ..parsers.docx_parser import extract_text_from_docx


def convert_docx_to_pdf_with_fitz(raw_text: str, output_path: str) -> str:
    """Generate professional PDF using PyMuPDF (fitz)."""
    import fitz

    doc = fitz.open()
    page_w, page_h = 595.0, 842.0  # A4 standard dimensions in points
    margin_x = 42.0
    margin_top = 45.0
    usable_w = page_w - (margin_x * 2)

    page = doc.new_page(width=page_w, height=page_h)
    y = margin_top
    lines = [l.strip() for l in raw_text.split("\n")]
    is_first_line = True

    for line in lines:
        if not line:
            y += 5
            continue

        # Check page height break
        if y > page_h - 55:
            page = doc.new_page(width=page_w, height=page_h)
            y = margin_top

        # Header - Candidate Name
        if is_first_line and len(line) < 60:
            page.insert_text(
                fitz.Point(margin_x, y + 14),
                line,
                fontsize=18,
                fontname="helv",
                color=(0.12, 0.16, 0.23), # Slate 800
            )
            y += 24
            is_first_line = False
            continue

        is_first_line = False

        # Section Headers (ALL CAPS or known CV sections)
        if (line.isupper() and len(line) < 45) or line in (
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
            y += 6
            if y > page_h - 55:
                page = doc.new_page(width=page_w, height=page_h)
                y = margin_top

            # Title text
            page.insert_text(
                fitz.Point(margin_x, y + 9),
                line.upper(),
                fontsize=10.5,
                fontname="helv",
                color=(0.31, 0.27, 0.90), # Indigo 600
            )
            # Underline line
            page.draw_line(
                fitz.Point(margin_x, y + 12),
                fitz.Point(margin_x + usable_w, y + 12),
                color=(0.85, 0.88, 0.92),
                width=0.75,
            )
            y += 18

        # Role / Company line
        elif " | " in line and len(line) < 100:
            y += 3
            if y > page_h - 55:
                page = doc.new_page(width=page_w, height=page_h)
                y = margin_top

            page.insert_text(
                fitz.Point(margin_x, y + 8),
                line,
                fontsize=9.5,
                fontname="helv",
                color=(0.12, 0.16, 0.23),
            )
            y += 13

        # Bullet points
        elif line.startswith("*") or line.startswith("-") or line.startswith("•"):
            bullet_clean = line.lstrip("*-• ")
            rect = fitz.Rect(margin_x + 12, y, margin_x + usable_w, y + 40)
            page.insert_text(
                fitz.Point(margin_x + 2, y + 7.5),
                "•",
                fontsize=10,
                fontname="helv",
                color=(0.31, 0.27, 0.90),
            )
            rc = page.insert_textbox(
                rect,
                bullet_clean,
                fontsize=9,
                fontname="helv",
                color=(0.28, 0.33, 0.41),
                lineheight=1.2,
            )
            # Height based on length
            lines_count = max(1, (len(bullet_clean) // 85) + 1)
            y += (lines_count * 11) + 2

        # Regular text paragraphs
        else:
            rect = fitz.Rect(margin_x, y, margin_x + usable_w, y + 80)
            rc = page.insert_textbox(
                rect,
                line,
                fontsize=9,
                fontname="helv",
                color=(0.20, 0.25, 0.33),
                lineheight=1.2,
            )
            lines_count = max(1, (len(line) // 90) + 1)
            y += (lines_count * 11) + 3

    # Add page numbers at the bottom
    for i, p in enumerate(doc):
        p.insert_text(
            fitz.Point(page_w / 2 - 15, page_h - 20),
            f"Page {i + 1}",
            fontsize=8,
            fontname="helv",
            color=(0.60, 0.60, 0.60),
        )

    doc.save(output_path)
    doc.close()
    return output_path


def convert_docx_to_pdf_with_fpdf2(raw_text: str, output_path: str) -> str:
    """Fallback generator using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", size=9)

    for line in raw_text.split("\n"):
        clean = line.encode("latin-1", "replace").decode("latin-1")
        if not clean.strip():
            pdf.ln(3)
        else:
            pdf.write(5, clean + "\n")

    pdf.output(output_path)
    return output_path


def convert_docx_to_pdf(docx_path: str, output_path: str) -> str:
    """Generate clean, valid PDF from DOCX using PyMuPDF with fpdf2 fallback."""
    raw_text = extract_text_from_docx(docx_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    try:
        return convert_docx_to_pdf_with_fitz(raw_text, output_path)
    except Exception as fitz_err:
        print(f"PyMuPDF generation note: {fitz_err}. Trying fpdf2 fallback.")
        return convert_docx_to_pdf_with_fpdf2(raw_text, output_path)
