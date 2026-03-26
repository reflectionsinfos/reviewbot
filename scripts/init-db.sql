-- Initialize PostgreSQL database for AI Review Agent
-- This script runs automatically on first database creation

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: Tables are created by SQLAlchemy migrations
-- This script is for database-level setup only

-- Create index for performance (optional - SQLAlchemy creates most)
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);
CREATE INDEX IF NOT EXISTS idx_reports_approval ON reports(approval_status);

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO review_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO review_user;
