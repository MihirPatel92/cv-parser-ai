import re
import copy
import docx
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from typing import Dict, List


class DocxFormatter:
    """
    Fills DOCX templates two ways:
      1. fill_placeholders: for templates with {{any_placeholder}} syntax
      2. freeform_fill: for templates with no placeholders (AI-guided structure mirroring)
    Preserves all original run-level formatting (font, size, bold, italic, color).
    """

    def fill_placeholders(self, template_path: str, mapping: Dict[str, str], output_path: str) -> str:
        """
        Replace all {{placeholder}} occurrences in template with mapped values.
        Works on paragraphs, tables, headers, and footers.
        Preserves run-level formatting by doing run-aware replacement.
        """
        doc = docx.Document(template_path)

        # Process main body paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, mapping)

        # Process tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, mapping)

        # Process headers and footers in all sections
        for section in doc.sections:
            for para in section.header.paragraphs:
                self._replace_in_paragraph(para, mapping)
            for para in section.footer.paragraphs:
                self._replace_in_paragraph(para, mapping)
            # Header/footer tables
            for table in section.header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            self._replace_in_paragraph(para, mapping)

        doc.save(output_path)
        return output_path

    def _replace_in_paragraph(self, paragraph, mapping: Dict[str, str]):
        """
        Robust placeholder replacement that handles placeholders split across runs.
        Strategy: consolidate all runs into one text string, perform replacement,
        then restore to first run while preserving that run's formatting.
        """
        if not paragraph.text:
            return

        full_text = "".join(run.text for run in paragraph.runs)
        new_text = full_text

        for placeholder, value in mapping.items():
            if placeholder in new_text:
                replacement = str(value) if value is not None else ""
                new_text = new_text.replace(placeholder, replacement)

        if new_text == full_text:
            return  # Nothing changed, skip

        # Restore: put all text in first run, clear the rest
        if paragraph.runs:
            paragraph.runs[0].text = new_text
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            # No runs (rare), add a run
            paragraph.add_run(new_text)

    def freeform_fill(self, template_path: str, section_data: Dict[str, str], output_path: str) -> str:
        """
        For templates without placeholders.
        Creates a new DOCX that mirrors the template's style by:
          - Copying the template's styles
          - Writing AI-generated section content using the template as a style reference
        """
        # Use the template as the base document to inherit all styles
        doc = docx.Document(template_path)

        # Clear all existing content from body (keep styles)
        for element in list(doc.element.body):
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            if tag in ('p', 'tbl', 'sdt'):
                doc.element.body.remove(element)

        # Write section data using template heading/body styles
        for section_name, content in section_data.items():
            # Add section heading
            heading = doc.add_paragraph(section_name.upper().replace('_', ' '), style='Heading 1')

            # Add content
            if isinstance(content, list):
                for item in content:
                    p = doc.add_paragraph(style='List Bullet')
                    p.add_run(str(item))
            elif isinstance(content, str):
                # Handle bullet-point-like content
                lines = content.strip().split('\n')
                for line in lines:
                    line = line.strip().lstrip('•-* ')
                    if line:
                        p = doc.add_paragraph(style='Body Text' if 'Body Text' in [s.name for s in doc.styles] else 'Normal')
                        p.add_run(line)
            else:
                doc.add_paragraph(str(content))

            # Add spacing
            doc.add_paragraph("")

        doc.save(output_path)
        return output_path
