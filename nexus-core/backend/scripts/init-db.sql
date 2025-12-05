-- NEXUS Database Initialization Script
-- Executed on first PostgreSQL container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema for application tables
CREATE SCHEMA IF NOT EXISTS nexus;

-- Set default search path
ALTER DATABASE nexus SET search_path TO nexus, public;

-- Grant privileges
GRANT ALL ON SCHEMA nexus TO nexus;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'NEXUS database initialized successfully';
END $$;
