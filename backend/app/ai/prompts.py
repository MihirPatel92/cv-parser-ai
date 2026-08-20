CV_EXTRACTION_PROMPT = """
You are a precise CV/Resume data extractor. Extract ALL information from the following CV text.
Return ONLY valid JSON matching this exact schema:
{
  "full_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "linkedin": "string or null",
  "website": "string or null",
  "professional_summary": "string or null",
  "skills": ["skill1", "skill2", ...],
  "technical_skills": ["skill1", ...],
  "soft_skills": ["skill1", ...],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "string",
      "end_date": "string or 'Present'",
      "location": "string or null",
      "responsibilities": ["bullet1", "bullet2", ...]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string or null",
      "start_date": "string or null",
      "end_date": "string or null",
      "gpa": "string or null"
    }
  ],
  "certifications": [{"name": "string", "issuer": "string or null", "date": "string or null"}],
  "languages": [{"language": "string", "proficiency": "string or null"}],
  "projects": [{"name": "string", "description": "string", "technologies": ["string"]}],
  "awards": ["string"],
  "publications": ["string"],
  "references": "string or null"
}

CV TEXT:
{cv_text}

Return ONLY the JSON object. No explanation, no markdown, no code blocks.
"""

PLACEHOLDER_MAPPING_PROMPT = """
You are a precise data mapping engine. You will map CV data to template placeholders.

The template contains these placeholders (in their exact original format):
{placeholders_list}

The extracted CV data is:
{cv_data_json}

Your task: Return a JSON object where each key is the EXACT placeholder text (as it appears in the template, including braces) and the value is the data to fill in.

Rules:
1. Match placeholders intelligently regardless of naming convention ({{name}}, {{candidate_name}}, {{full_name}} all mean the person's name)
2. For skill1, skill2, skill3... populate with the first, second, third skill respectively
3. For experience fields like {{company1}}, {{company2}} - populate with first job, second job etc.
4. If a placeholder has no matching data, use empty string ""
5. For multi-line content (responsibilities, summary), format as clean text
6. Return ONLY valid JSON. Keys must be EXACTLY the placeholder strings including {{ and }}

Return format:
{{"{{placeholder1}}": "value1", "{{placeholder2}}": "value2"}}
"""

STRUCTURE_ANALYSIS_PROMPT = """
Analyze this template document text and identify its structure/sections.
Return JSON with the sections found:
{"sections": ["Summary", "Skills", "Experience", "Education"], "has_placeholders": false}

Template text:
{template_text}

Return ONLY the JSON object. No explanation, no markdown, no code blocks.
"""

FREEFORM_MAPPING_PROMPT = """
You are an expert CV formatter. The company template has this structure:
{template_structure}

The candidate's CV data is:
{cv_data_json}

Rewrite the candidate's CV following EXACTLY the company template's section order and style.
Return a JSON object with each section filled with the candidate's data:
{"section_name": "formatted content"}

Keep the same section names as in the template. Format experience with bullet points.
Return ONLY the JSON object. No explanation, no markdown, no code blocks.
"""
