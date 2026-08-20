-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enums
CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'recruiter');
CREATE TYPE conversion_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE ai_provider_type AS ENUM ('gemini', 'openai', 'ollama');
CREATE TYPE placeholder_type AS ENUM ('auto_detected', 'manual', 'none');
CREATE TYPE output_format AS ENUM ('docx', 'pdf', 'both');

-- users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'recruiter',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- cv_templates table
CREATE TABLE cv_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    company_name VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size_bytes BIGINT,
    placeholder_type placeholder_type DEFAULT 'auto_detected',
    detected_placeholders JSONB DEFAULT '[]',
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- conversions table
CREATE TABLE conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id UUID REFERENCES users(id) ON DELETE SET NULL,
    template_id UUID REFERENCES cv_templates(id) ON DELETE SET NULL,
    source_cv_path VARCHAR(500) NOT NULL,
    source_cv_filename VARCHAR(255) NOT NULL,
    source_cv_file_type VARCHAR(10) NOT NULL,
    output_docx_path VARCHAR(500),
    output_pdf_path VARCHAR(500),
    output_format output_format NOT NULL DEFAULT 'docx',
    status conversion_status NOT NULL DEFAULT 'pending',
    ai_provider ai_provider_type NOT NULL DEFAULT 'gemini',
    ai_model_used VARCHAR(100),
    extracted_cv_data JSONB,
    placeholder_mapping JSONB,
    processing_time_seconds FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ai_model_configs table
CREATE TABLE ai_model_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider ai_provider_type NOT NULL DEFAULT 'gemini',
    model_name VARCHAR(100) NOT NULL DEFAULT 'gemini-1.5-flash',
    api_key_encrypted TEXT,
    ollama_base_url VARCHAR(255) DEFAULT 'http://localhost:11434',
    is_active BOOLEAN NOT NULL DEFAULT true,
    temperature FLOAT DEFAULT 0.1,
    max_tokens INTEGER DEFAULT 4096,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_conversions_recruiter ON conversions(recruiter_id);
CREATE INDEX idx_conversions_status ON conversions(status);
CREATE INDEX idx_conversions_created ON conversions(created_at DESC);
CREATE INDEX idx_templates_uploaded_by ON cv_templates(uploaded_by);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON cv_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_config_updated_at BEFORE UPDATE ON ai_model_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed: default super admin (password: Admin@123)
-- bcrypt hash of Admin@123
INSERT INTO users (id, email, full_name, hashed_password, role) VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin@cvparser.com', 'Super Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TgxwjBLbZ.HE9v.dxXTZNXAU1O7m', 'super_admin')
ON CONFLICT (email) DO NOTHING;

-- Default AI config
INSERT INTO ai_model_configs (provider, model_name, is_active, temperature, max_tokens) VALUES
    ('gemini', 'gemini-1.5-flash', true, 0.1, 4096)
ON CONFLICT DO NOTHING;
