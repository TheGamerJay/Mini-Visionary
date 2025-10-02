-- Secure Auth & Credits System Migration
-- Run this once on your Railway PostgreSQL database

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  credits INT NOT NULL DEFAULT 20,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create image_jobs table with binary storage
CREATE TABLE IF NOT EXISTS image_jobs (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind VARCHAR(32) NOT NULL,  -- 'generate', 'edit', 'variation', 'remix'
  prompt TEXT NOT NULL,
  size VARCHAR(16) DEFAULT '1024x1024',
  image_png BYTEA NOT NULL,
  credits_used INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Performance index for history queries
CREATE INDEX IF NOT EXISTS idx_image_jobs_user_created
ON image_jobs (user_id, created_at DESC);

-- Seed credits for any existing users (safe to run multiple times)
UPDATE users SET credits = COALESCE(credits, 0) WHERE credits IS NULL;

-- Email index for faster login
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

COMMENT ON TABLE users IS 'User accounts with JWT auth and credit balance';
COMMENT ON TABLE image_jobs IS 'Generated images stored as PNG binary data';
COMMENT ON COLUMN image_jobs.kind IS 'Operation type: generate, edit, variation, remix';
COMMENT ON COLUMN image_jobs.image_png IS 'Binary PNG data stored in database';
