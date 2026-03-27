-- ============================================
-- ReviewBot v2.0 - Simple Database Setup
-- ============================================
-- This script runs on first PostgreSQL startup

-- Use md5 for broader client compatibility (DBeaver, etc.)
SET password_encryption = 'md5';

-- Create user (will be skipped if exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'review_user') THEN
        CREATE ROLE review_user LOGIN PASSWORD 'review_password_change_me';
    END IF;
END$$;

-- Create database (will be skipped if exists)
SELECT 'CREATE DATABASE reviews_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'reviews_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE reviews_db TO review_user;

-- Connect and grant schema access
\c reviews_db
GRANT ALL ON SCHEMA public TO review_user;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'ReviewBot database setup complete!';
    RAISE NOTICE 'Database: reviews_db';
    RAISE NOTICE 'User: review_user';
    RAISE NOTICE 'Password: review_password_change_me';
END$$;
