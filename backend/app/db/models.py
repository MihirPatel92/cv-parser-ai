import enum
import uuid as uuid_pkg
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    recruiter = "recruiter"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.recruiter)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    templates_uploaded = relationship("CVTemplate", back_populates="uploader", foreign_keys="CVTemplate.uploaded_by")
    conversions = relationship("Conversion", back_populates="recruiter", foreign_keys="Conversion.recruiter_id")


class CVTemplate(Base):
    __tablename__ = "cv_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    company_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False, default="template.docx")
    file_type = Column(String(10), nullable=False)  # 'docx' or 'pdf'
    file_size_bytes = Column(Integer, nullable=True)
    placeholder_type = Column(String(20), nullable=False, default="auto_detected")  # auto_detected | none
    detected_placeholders = Column(JSON, default=list)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploader = relationship("User", back_populates="templates_uploaded", foreign_keys=[uploaded_by])
    conversions = relationship("Conversion", back_populates="template", foreign_keys="Conversion.template_id")


class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("cv_templates.id"), nullable=True)
    source_cv_path = Column(String(500), nullable=False)
    source_cv_filename = Column(String(255), nullable=False)
    source_cv_file_type = Column(String(10), nullable=False, default="pdf")
    output_docx_path = Column(String(500), nullable=True)
    output_pdf_path = Column(String(500), nullable=True)
    output_format = Column(String(10), nullable=False, default="both")  # docx | pdf | both
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    ai_provider = Column(String(20), nullable=False, default="gemini")
    ai_model_used = Column(String(100), nullable=True)
    extracted_cv_data = Column(JSON, nullable=True)
    placeholder_mapping = Column(JSON, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    recruiter = relationship("User", back_populates="conversions", foreign_keys=[recruiter_id])
    template = relationship("CVTemplate", back_populates="conversions", foreign_keys=[template_id])


class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    provider = Column(String(20), nullable=False, default="gemini")  # gemini | openai | ollama
    model_name = Column(String(100), nullable=False, default="gemini-1.5-flash")
    api_key_encrypted = Column(Text, nullable=True)  # stored as plaintext for now; encrypt in prod
    ollama_base_url = Column(String(255), nullable=True, default="http://localhost:11434")
    is_active = Column(Boolean, default=True)
    temperature = Column(Float, nullable=False, default=0.1)
    max_tokens = Column(Integer, nullable=True, default=4096)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
