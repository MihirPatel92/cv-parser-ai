CV_EXTRACTION_PROMPT = """
You are a precise, comprehensive CV/Resume data extractor. Extract ALL information from the following CV text.
Return ONLY valid JSON matching this exact structure:
{
  "full_name": "Full Name of Candidate",
  "first_name": "First Name",
  "last_name": "Last Name",
  "job_title": "Primary Job Title / Professional Headline",
  "email": "Email address or null",
  "phone": "Phone number or null",
  "city": "City or null",
  "country": "Country or null",
  "location": "Location (City, Country) or null",
  "linkedin": "LinkedIn profile URL or username or null",
  "github": "GitHub URL or username or null",
  "portfolio": "Portfolio or personal website or null",
  "professional_summary": "Complete professional summary statement",
  "core_competencies": ["Competency 1", "Competency 2", ...],
  "skills": ["Skill 1", "Skill 2", ...],
  "languages": ["Language 1", "Language 2", ...],
  "frameworks": ["Framework 1", "Framework 2", ...],
  "cloud_devops": ["Cloud/Tool 1", "Cloud/Tool 2", ...],
  "databases": ["Database 1", "Database 2", ...],
  "architecture_patterns": ["Pattern 1", "Pattern 2", ...],
  "strengths": ["Strength 1", "Strength 2", ...],
  "technical_skills": {
    "languages": ["C#", "Python", ...],
    "frameworks": [".NET Core", "Flask", ...],
    "frontend": ["React.js", "Angular", ...],
    "ai_ml": ["PyTorch", "LLMs", "RAG", ...],
    "databases": ["SQL Server", "PostgreSQL", ...],
    "cloud_devops": ["Azure", "AWS", "Docker", ...],
    "tools": ["Git", "Jira", "ALM", ...]
  },
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "Start Date",
      "end_date": "End Date or Present",
      "location": "Location",
      "team_or_domain": "Team size or Domain area",
      "bullets": [
        "Action verb project scope and business impact",
        "Technical architecture design and optimization metric",
        "Cross-functional collaboration, CI/CD or code quality",
        "Mentorship, code reviews or engineering best practices"
      ]
    }
  ],
  "projects": [
    {
      "title": "Project Title / Name",
      "tech_stack": "Tech Stack used",
      "link": "Link or demo if available",
      "bullets": [
        "Architectural highlight and scalability",
        "Key features, integration and impact metrics"
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University / Institution Name",
      "graduation_year": "Year",
      "gpa": "GPA or Score or null"
    }
  ],
  "certifications": [
    {
      "title": "Certification Title (e.g. PMP, SAFe Agilist)",
      "issuer": "Issuer Organization",
      "year": "Year"
    }
  ],
  "spoken_languages": [
    {
      "language": "English",
      "proficiency": "Professional"
    }
  ]
}

CV TEXT TO EXTRACT:
{cv_text}

Return ONLY valid JSON. Do not include markdown code blocks, backticks, or explanatory text.
"""

PLACEHOLDER_MAPPING_PROMPT = """
You are an intelligent CV template data mapper. Your task is to map extracted candidate CV data to exact template placeholder tags.

TEMPLATE PLACEHOLDERS DETECTED (in their exact original format):
{placeholders_list}

CANDIDATE CV DATA:
{cv_data_json}

INSTRUCTIONS:
1. Return a single JSON object where EVERY key is EXACTLY the placeholder string (including braces `{{` and `}}`).
2. Map fields intelligently:
   - `{{First_Name}}` -> Candidate's first name
   - `{{Last_Name}}` -> Candidate's last name
   - `{{JOB_TITLE}}` -> Primary job title / target role
   - `{{City}}`, `{{Country}}`, `{{Email_Address}}`, `{{Phone_Number}}`, `{{LinkedIn_URL}}`, `{{GitHub_URL}}`, `{{Portfolio_URL}}` -> Candidate's contact info
   - `{{Language_1}}`, `{{Language_2}}`, ... -> Programming languages from skills
   - `{{Framework_1}}`, `{{Framework_2}}`, ... -> Web frameworks / technologies
   - `{{Cloud_1}}`, `{{DevOps_Tool_1}}`, ... -> Cloud and DevOps tools
   - `{{Database_1}}`, `{{Database_2}}`, ... -> Database systems
   - `{{Architecture_Pattern_1}}`, ... -> Architecture / design patterns or core competencies
   - `{{Strength_1}}`, `{{Strength_2}}`, ... -> Core strengths / competencies
   - `{{Professional_Summary_...}}` (any long summary placeholder) -> Full professional summary text
   - `{{Role_1_Job_Title}}`, `{{Role_1_Company_Name}}`, `{{Role_1_Start_Date}}`, `{{Role_1_End_Date}}`, `{{Role_1_Team_Or_Domain}}`, `{{Role_1_Location}}` -> Details from most recent job
   - `{{Role_1_Bullet_1_...}}`, `{{Role_1_Bullet_2_...}}`, ... -> Distinct bullet points from job 1
   - `{{Role_2_...}}`, `{{Role_3_...}}` -> Corresponding details from job 2, job 3, etc.
   - `{{Project_1_Title}}`, `{{Project_1_Tech_Stack}}`, `{{Project_1_Description_Bullet_1_...}}` -> Projects details
   - `{{Degree_Name}}`, `{{University_Name}}`, `{{Graduation_Year}}`, `{{GPA_Score}}` -> Primary education
   - `{{Secondary_Degree_Name}}`, `{{Secondary_Institution}}`, `{{Secondary_Grad_Year}}` -> Secondary education
   - `{{Certification_1_Title}}`, `{{Cert_1_Issuer}}`, `{{Cert_1_Year}}` -> Certification 1
   - `{{Certification_2_Title}}`, `{{Cert_2_Issuer}}`, `{{Cert_2_Year}}` -> Certification 2
   - `{{Certification_3_Title}}`, `{{Cert_3_Issuer}}`, `{{Cert_3_Year}}` -> Certification 3
3. For any placeholder with no corresponding candidate data, set value to empty string `""` (do NOT leave placeholder tag or null).
4. Return ONLY valid JSON format:
{
  "{{First_Name}}": "Mihir",
  "{{Last_Name}}": "Patel",
  ...
}
"""

STRUCTURE_ANALYSIS_PROMPT = """
Analyze this CV template document and identify its section structure.
Return JSON with the sections found:
{
  "sections": ["Professional Summary", "Technical Skills", "Professional Experience", "Education", "Certifications", "Projects"],
  "has_placeholders": false
}

Template text:
{template_text}

Return ONLY valid JSON.
"""

FREEFORM_MAPPING_PROMPT = """
You are an expert CV formatter. The target company template uses this structure:
{template_structure}

The candidate's CV data is:
{cv_data_json}

Rewrite and re-sequence the candidate's CV data to match the target template's sections and styling.
Return a JSON object where each key is the section name and value is the formatted content:
{
  "PROFESSIONAL SUMMARY": "...",
  "TECHNICAL SKILLS": "...",
  "PROFESSIONAL EXPERIENCE": "...",
  "EDUCATION": "..."
}

Return ONLY valid JSON.
"""
