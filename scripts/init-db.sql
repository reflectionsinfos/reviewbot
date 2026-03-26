-- ============================================
-- ReviewBot v2.0 - Database Initialization
-- ============================================
-- This script runs automatically when PostgreSQL container starts

-- Create database for ReviewBot
SELECT 'CREATE DATABASE reviews_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'reviews_db')\gexec

-- Create user if not exists
DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'review_user') THEN
      CREATE ROLE review_user LOGIN PASSWORD 'review_password_change_me';
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE reviews_db TO review_user;

-- Connect to the database
\c reviews_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO review_user;

-- Create extension for UUID (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set search path
ALTER USER review_user SET search_path TO public;

-- Log success
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'ReviewBot Database Initialized!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database: reviews_db';
    RAISE NOTICE 'User: review_user';
    RAISE NOTICE 'Password: review_password_change_me';
    RAISE NOTICE 'Host: localhost';
    RAISE NOTICE 'Port: 5432';
    RAISE NOTICE '========================================';
END $$;
