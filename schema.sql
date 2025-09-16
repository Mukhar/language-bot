-- Healthcare Language Support Bot Database Schema
-- Compatible with both SQLite and PostgreSQL

-- Scenarios table
CREATE TABLE scenarios (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,  -- general, emergency, routine
    difficulty VARCHAR(20) NOT NULL, -- beginner, intermediate
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for scenarios
CREATE INDEX ix_scenarios_id ON scenarios (id);

-- Responses table
CREATE TABLE responses (
    id VARCHAR(36) PRIMARY KEY,
    scenario_id VARCHAR(36) NOT NULL,  -- Foreign key reference to scenarios.id
    response_text TEXT NOT NULL,
    score REAL,  -- 1-10 scale (REAL for SQLite compatibility, FLOAT for PostgreSQL)
    feedback TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for responses
CREATE INDEX ix_responses_id ON responses (id);
CREATE INDEX ix_responses_scenario_id ON responses (scenario_id);

-- Insert sample data
INSERT INTO scenarios (id, title, description, category, difficulty) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'Patient Intake', 'A patient arrives for their first appointment. Practice basic greeting and information gathering.', 'general', 'beginner'),
('550e8400-e29b-41d4-a716-446655440002', 'Emergency Triage', 'A patient comes to the emergency department with chest pain. Practice urgent care communication.', 'emergency', 'intermediate'),
('550e8400-e29b-41d4-a716-446655440003', 'Routine Checkup', 'A patient is here for their annual physical exam. Practice general health discussion.', 'routine', 'beginner');