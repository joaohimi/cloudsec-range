BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

CREATE TABLE curriculum_tracks (
    id UUID NOT NULL, 
    code VARCHAR(50) NOT NULL, 
    title VARCHAR(160) NOT NULL, 
    description TEXT, 
    position INTEGER NOT NULL, 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_curriculum_tracks_code ON curriculum_tracks (code);

CREATE TABLE curriculum_modules (
    id UUID NOT NULL, 
    track_id UUID NOT NULL, 
    code VARCHAR(80) NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    description TEXT, 
    position INTEGER NOT NULL, 
    canonical_source VARCHAR(500), 
    source_verified BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(track_id) REFERENCES curriculum_tracks (id) ON DELETE CASCADE, 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_curriculum_modules_code ON curriculum_modules (code);

CREATE TABLE competencies (
    id UUID NOT NULL, 
    module_id UUID NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    description TEXT NOT NULL, 
    learning_requirements JSONB DEFAULT '[]'::jsonb NOT NULL, 
    internship_requirements JSONB DEFAULT '[]'::jsonb NOT NULL, 
    is_security_relevant BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE CASCADE, 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_competencies_code ON competencies (code);

CREATE TABLE learning_resources (
    id UUID NOT NULL, 
    module_id UUID, 
    competency_id UUID, 
    resource_type VARCHAR(40) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    url VARCHAR(1000) NOT NULL, 
    publisher VARCHAR(160), 
    product_version VARCHAR(80), 
    last_verified_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE SET NULL, 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE SET NULL
);

CREATE TABLE internship_tickets (
    id UUID NOT NULL, 
    ticket_key VARCHAR(40) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    department VARCHAR(100) NOT NULL, 
    priority VARCHAR(20) NOT NULL, 
    status VARCHAR(30) DEFAULT 'backlog' NOT NULL, 
    description TEXT NOT NULL, 
    business_impact TEXT, 
    acceptance_criteria JSONB DEFAULT '[]'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (ticket_key)
);

CREATE UNIQUE INDEX ix_internship_tickets_ticket_key ON internship_tickets (ticket_key);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial') RETURNING alembic_version.version_num;

-- Running upgrade 0001_initial -> 0002_curriculum_engine

CREATE TABLE curriculum_versions (
    id UUID NOT NULL, 
    code VARCHAR(60) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    source_filename VARCHAR(500) NOT NULL, 
    source_checksum VARCHAR(128), 
    status VARCHAR(20) DEFAULT 'active' NOT NULL, 
    import_notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_curriculum_versions_code ON curriculum_versions (code);

ALTER TABLE curriculum_tracks ADD COLUMN version_id UUID;

ALTER TABLE curriculum_tracks ADD CONSTRAINT fk_curriculum_tracks_version_id FOREIGN KEY(version_id) REFERENCES curriculum_versions (id) ON DELETE SET NULL;

CREATE TABLE curriculum_blocks (
    id UUID NOT NULL, 
    track_id UUID NOT NULL, 
    code VARCHAR(30) NOT NULL, 
    title VARCHAR(160) NOT NULL, 
    position INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_curriculum_block_track_code UNIQUE (track_id, code), 
    FOREIGN KEY(track_id) REFERENCES curriculum_tracks (id) ON DELETE CASCADE
);

CREATE INDEX ix_curriculum_blocks_track_id ON curriculum_blocks (track_id);

ALTER TABLE curriculum_modules ADD COLUMN block_id UUID;

ALTER TABLE curriculum_modules ADD COLUMN source_module_code VARCHAR(40);

ALTER TABLE curriculum_modules ADD COLUMN estimated_hours INTEGER;

ALTER TABLE curriculum_modules ADD COLUMN content_status VARCHAR(30) DEFAULT 'not_authored' NOT NULL;

ALTER TABLE curriculum_modules ADD CONSTRAINT fk_curriculum_modules_block_id FOREIGN KEY(block_id) REFERENCES curriculum_blocks (id) ON DELETE SET NULL;

CREATE TABLE curriculum_topics (
    id UUID NOT NULL, 
    module_id UUID NOT NULL, 
    code VARCHAR(80) NOT NULL, 
    title VARCHAR(220) NOT NULL, 
    position INTEGER NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_curriculum_topic_module_code UNIQUE (module_id, code), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE CASCADE
);

CREATE INDEX ix_curriculum_topics_module_id ON curriculum_topics (module_id);

ALTER TABLE competencies ADD COLUMN topic_id UUID;

ALTER TABLE competencies ADD CONSTRAINT fk_competencies_topic_id FOREIGN KEY(topic_id) REFERENCES curriculum_topics (id) ON DELETE SET NULL;

CREATE TABLE lessons (
    id UUID NOT NULL, 
    module_id UUID NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    sequence INTEGER NOT NULL, 
    summary TEXT, 
    content_markdown TEXT, 
    status VARCHAR(30) DEFAULT 'not_authored' NOT NULL, 
    official_sources_reviewed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_lesson_module_code UNIQUE (module_id, code), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE CASCADE
);

CREATE INDEX ix_lessons_module_id ON lessons (module_id);

CREATE TABLE labs (
    id UUID NOT NULL, 
    module_id UUID, 
    track_id UUID, 
    code VARCHAR(100) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    description TEXT, 
    environment VARCHAR(120) DEFAULT 'WSL2 Ubuntu 24.04' NOT NULL, 
    safety_profile VARCHAR(50) DEFAULT 'local-safe' NOT NULL, 
    estimated_minutes INTEGER, 
    manifest JSONB DEFAULT '{}'::jsonb NOT NULL, 
    status VARCHAR(30) DEFAULT 'planned' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_lab_has_track_or_module CHECK (module_id IS NOT NULL OR track_id IS NOT NULL), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE CASCADE, 
    FOREIGN KEY(track_id) REFERENCES curriculum_tracks (id) ON DELETE CASCADE, 
    UNIQUE (code)
);

CREATE INDEX ix_labs_module_id ON labs (module_id);

CREATE INDEX ix_labs_track_id ON labs (track_id);

CREATE UNIQUE INDEX ix_labs_code ON labs (code);

CREATE TABLE assessments (
    id UUID NOT NULL, 
    module_id UUID NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    assessment_type VARCHAR(40) NOT NULL, 
    total_points INTEGER DEFAULT '100' NOT NULL, 
    mastery_threshold FLOAT DEFAULT '80' NOT NULL, 
    rubric JSONB DEFAULT '{}'::jsonb NOT NULL, 
    status VARCHAR(30) DEFAULT 'planned' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE CASCADE, 
    UNIQUE (code)
);

CREATE INDEX ix_assessments_module_id ON assessments (module_id);

CREATE UNIQUE INDEX ix_assessments_code ON assessments (code);

CREATE TABLE lesson_competencies (
    lesson_id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    PRIMARY KEY (lesson_id, competency_id), 
    FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE, 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE TABLE lab_competencies (
    lab_id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    PRIMARY KEY (lab_id, competency_id), 
    FOREIGN KEY(lab_id) REFERENCES labs (id) ON DELETE CASCADE, 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE TABLE assessment_competencies (
    assessment_id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    PRIMARY KEY (assessment_id, competency_id), 
    FOREIGN KEY(assessment_id) REFERENCES assessments (id) ON DELETE CASCADE, 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE TABLE ticket_competencies (
    ticket_id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    PRIMARY KEY (ticket_id, competency_id), 
    FOREIGN KEY(ticket_id) REFERENCES internship_tickets (id) ON DELETE CASCADE, 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE TABLE competency_prerequisites (
    competency_id UUID NOT NULL, 
    prerequisite_id UUID NOT NULL, 
    PRIMARY KEY (competency_id, prerequisite_id), 
    CONSTRAINT ck_competency_not_own_prerequisite CHECK (competency_id <> prerequisite_id), 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE, 
    FOREIGN KEY(prerequisite_id) REFERENCES competencies (id) ON DELETE CASCADE
);

ALTER TABLE internship_tickets ADD COLUMN module_id UUID;

ALTER TABLE internship_tickets ADD COLUMN asset_context TEXT;

ALTER TABLE internship_tickets ADD COLUMN assigned_role VARCHAR(120);

ALTER TABLE internship_tickets ADD COLUMN initial_state TEXT;

ALTER TABLE internship_tickets ADD COLUMN investigation_steps JSONB DEFAULT '[]'::jsonb NOT NULL;

ALTER TABLE internship_tickets ADD COLUMN execution_steps JSONB DEFAULT '[]'::jsonb NOT NULL;

ALTER TABLE internship_tickets ADD COLUMN validation_steps JSONB DEFAULT '[]'::jsonb NOT NULL;

ALTER TABLE internship_tickets ADD COLUMN safety_scope TEXT;

ALTER TABLE internship_tickets ADD CONSTRAINT fk_internship_tickets_module_id FOREIGN KEY(module_id) REFERENCES curriculum_modules (id) ON DELETE SET NULL;

CREATE TABLE assessment_attempts (
    id UUID NOT NULL, 
    assessment_id UUID NOT NULL, 
    learner_key VARCHAR(80) DEFAULT 'primary' NOT NULL, 
    score FLOAT NOT NULL, 
    passed BOOLEAN DEFAULT false NOT NULL, 
    answers JSONB DEFAULT '{}'::jsonb NOT NULL, 
    feedback JSONB DEFAULT '{}'::jsonb NOT NULL, 
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_assessment_attempt_score_range CHECK (score >= 0 AND score <= 100), 
    FOREIGN KEY(assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
);

CREATE INDEX ix_assessment_attempts_assessment_id ON assessment_attempts (assessment_id);

CREATE TABLE coverage_requirements (
    id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    center VARCHAR(20) NOT NULL, 
    requirement_code VARCHAR(80) NOT NULL, 
    title VARCHAR(220) NOT NULL, 
    is_required BOOLEAN DEFAULT true NOT NULL, 
    status VARCHAR(30) DEFAULT 'missing' NOT NULL, 
    reviewer_note TEXT, 
    verified_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_coverage_requirement_key UNIQUE (competency_id, center, requirement_code), 
    CONSTRAINT ck_coverage_center CHECK (center IN ('learning', 'internship')), 
    CONSTRAINT ck_coverage_status CHECK (status IN ('missing', 'draft', 'ready', 'verified', 'not_applicable')), 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE INDEX ix_coverage_requirements_competency_id ON coverage_requirements (competency_id);

CREATE TABLE competency_progress (
    id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    learner_key VARCHAR(80) DEFAULT 'primary' NOT NULL, 
    status VARCHAR(30) DEFAULT 'not_started' NOT NULL, 
    mastery_score FLOAT, 
    notes TEXT, 
    last_assessed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_competency_progress_learner UNIQUE (competency_id, learner_key), 
    CONSTRAINT ck_mastery_score_range CHECK (mastery_score IS NULL OR (mastery_score >= 0 AND mastery_score <= 100)), 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE
);

CREATE INDEX ix_competency_progress_competency_id ON competency_progress (competency_id);

CREATE TABLE evidence (
    id UUID NOT NULL, 
    competency_id UUID NOT NULL, 
    lesson_id UUID, 
    lab_id UUID, 
    ticket_id UUID, 
    assessment_attempt_id UUID, 
    evidence_type VARCHAR(40) NOT NULL, 
    title VARCHAR(240) NOT NULL, 
    artifact_uri VARCHAR(1000), 
    summary TEXT, 
    sanitized BOOLEAN DEFAULT false NOT NULL, 
    review_status VARCHAR(30) DEFAULT 'pending' NOT NULL, 
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_evidence_has_source CHECK (lesson_id IS NOT NULL OR lab_id IS NOT NULL OR ticket_id IS NOT NULL OR assessment_attempt_id IS NOT NULL), 
    FOREIGN KEY(competency_id) REFERENCES competencies (id) ON DELETE CASCADE, 
    FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE SET NULL, 
    FOREIGN KEY(lab_id) REFERENCES labs (id) ON DELETE SET NULL, 
    FOREIGN KEY(ticket_id) REFERENCES internship_tickets (id) ON DELETE SET NULL, 
    FOREIGN KEY(assessment_attempt_id) REFERENCES assessment_attempts (id) ON DELETE SET NULL
);

CREATE INDEX ix_evidence_competency_id ON evidence (competency_id);

UPDATE alembic_version SET version_num='0002_curriculum_engine' WHERE alembic_version.version_num = '0001_initial';

-- Running upgrade 0002_curriculum_engine -> 0003_platform_core

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR(320) NOT NULL, 
    display_name VARCHAR(160) NOT NULL, 
    password_hash VARCHAR(512) NOT NULL, 
    status VARCHAR(20) DEFAULT 'active' NOT NULL, 
    last_login_at TIMESTAMP WITH TIME ZONE, 
    password_changed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_users_email UNIQUE (email), 
    CONSTRAINT ck_users_status CHECK (status IN ('active', 'disabled', 'pending'))
);

CREATE INDEX ix_users_status ON users (status);

CREATE TABLE roles (
    id UUID NOT NULL, 
    code VARCHAR(60) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    description TEXT, 
    is_system BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_roles_code UNIQUE (code)
);

CREATE TABLE permissions (
    id UUID NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    name VARCHAR(160) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_permissions_code UNIQUE (code)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL, 
    role_id UUID NOT NULL, 
    PRIMARY KEY (user_id, role_id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL, 
    permission_id UUID NOT NULL, 
    PRIMARY KEY (role_id, permission_id), 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
    FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

CREATE TABLE auth_sessions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    token_hash VARCHAR(64) NOT NULL, 
    csrf_token_hash VARCHAR(64) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    last_seen_at TIMESTAMP WITH TIME ZONE, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    ip_address VARCHAR(64), 
    user_agent VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_auth_sessions_token_hash UNIQUE (token_hash), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_auth_sessions_user_expires ON auth_sessions (user_id, expires_at);

CREATE TABLE audit_events (
    id UUID NOT NULL, 
    actor_user_id UUID, 
    action VARCHAR(120) NOT NULL, 
    target_type VARCHAR(80), 
    target_id VARCHAR(120), 
    outcome VARCHAR(30) DEFAULT 'success' NOT NULL, 
    source_ip VARCHAR(64), 
    user_agent VARCHAR(500), 
    details JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_audit_events_created_at ON audit_events (created_at);

CREATE INDEX ix_audit_events_actor_created ON audit_events (actor_user_id, created_at);

CREATE INDEX ix_audit_events_action ON audit_events (action);

INSERT INTO roles (id, code, name, description, is_system) VALUES (gen_random_uuid(), 'owner', 'Owner', 'Administração integral da plataforma.', true), (gen_random_uuid(), 'learner', 'Learner', 'Aprendizagem, laboratórios, submissões e portfólio próprio.', true), (gen_random_uuid(), 'reviewer', 'Reviewer', 'Revisão técnica de tickets, avaliações e evidências.', true);

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'platform:admin', 'Administrar plataforma', 'Acesso administrativo global.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'users:manage', 'Gerir utilizadores', 'Criar, desativar e atribuir funções a utilizadores.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'audit:read', 'Consultar auditoria', 'Consultar eventos de auditoria.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'learning:read', 'Consultar aprendizagem', 'Aceder ao conteúdo do Learning Center.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'learning:progress', 'Registar progresso', 'Registar progresso e domínio de competências.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'labs:execute', 'Executar laboratórios', 'Executar laboratórios autorizados.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'tickets:read', 'Consultar tickets', 'Consultar tickets do Internship Center.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'tickets:submit', 'Submeter tickets', 'Criar e submeter trabalho profissional simulado.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'tickets:review', 'Rever tickets', 'Rever e classificar tickets submetidos.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'assessments:attempt', 'Realizar avaliações', 'Submeter tentativas de avaliação.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'assessments:review', 'Rever avaliações', 'Corrigir e validar avaliações.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'portfolio:read', 'Consultar portfólio', 'Consultar evidências e portfólio autorizado.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'portfolio:manage', 'Gerir portfólio', 'Gerir evidências próprias.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'portfolio:review', 'Rever portfólio', 'Rever evidências de outros utilizadores.');

INSERT INTO permissions (id, code, name, description) VALUES (gen_random_uuid(), 'sessions:manage', 'Gerir sessões', 'Consultar e revogar sessões próprias.');

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'assessments:attempt';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'assessments:review';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'audit:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'labs:execute';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'learning:progress';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'learning:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'platform:admin';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'portfolio:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'portfolio:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'portfolio:review';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'sessions:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'tickets:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'tickets:review';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'tickets:submit';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'owner' AND p.code = 'users:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'assessments:attempt';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'labs:execute';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'learning:progress';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'learning:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'portfolio:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'portfolio:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'sessions:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'tickets:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'learner' AND p.code = 'tickets:submit';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'assessments:review';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'labs:execute';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'learning:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'portfolio:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'portfolio:review';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'sessions:manage';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'tickets:read';

INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.code = 'reviewer' AND p.code = 'tickets:review';

UPDATE alembic_version SET version_num='0003_platform_core' WHERE alembic_version.version_num = '0002_curriculum_engine';

COMMIT;

