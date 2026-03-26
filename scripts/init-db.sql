-- ============================================
-- ReviewBot v2.0 - Database Initialization
-- ============================================
-- This script runs automatically when the PostgreSQL
-- container is first created.

-- Create database for ReviewBot
CREATE DATABASE reviews_db;

-- Connect to the database
\c reviews_db;

-- Create extension for UUID (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE reviews_db TO review_user;

-- Set search path
ALTER USER review_user SET search_path TO public;

-- Create schema comment
COMMENT ON DATABASE reviews_db IS 'ReviewBot v2.0 - AI Tech & Delivery Review Agent Database';

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'ReviewBot database initialized successfully!';
    RAISE NOTICE 'Database: reviews_db';
    RAISE NOTICE 'User: review_user';
END $$;
