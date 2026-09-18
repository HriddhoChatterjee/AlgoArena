CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE match_status AS ENUM ('waiting', 'active', 'completed', 'aborted');
CREATE TYPE event_type AS ENUM ('compile_error', 'syntax_shield_used', 'test_passed', 'airdrop_triggered', 'shoutcast_message');

-- Tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    elo_rating INTEGER NOT NULL DEFAULT 1200,
    college_campus VARCHAR(255),
    academic_section VARCHAR(255),
    equipped_perk VARCHAR(255),
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    total_solved INTEGER NOT NULL DEFAULT 0,
    current_streak INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status match_status NOT NULL DEFAULT 'waiting',
    player1_id UUID REFERENCES users(id) ON DELETE SET NULL,
    player2_id UUID REFERENCES users(id) ON DELETE SET NULL,
    winner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    problem_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE match_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type event_type NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_elo ON users(elo_rating DESC);
CREATE INDEX idx_users_campus_elo ON users(college_campus, elo_rating DESC);
CREATE INDEX idx_users_section_elo ON users(academic_section, elo_rating DESC);

CREATE INDEX idx_matches_problem_data ON matches USING GIN (problem_data);
CREATE INDEX idx_matches_player1 ON matches(player1_id);
CREATE INDEX idx_matches_player2 ON matches(player2_id);
CREATE INDEX idx_matches_status ON matches(status);

CREATE INDEX idx_match_events_match_id ON match_events(match_id);

-- Materialized View for Leaderboard Caching
CREATE MATERIALIZED VIEW leaderboard_cache AS
SELECT 
    id AS user_id,
    username,
    college_campus,
    academic_section,
    elo_rating,
    RANK() OVER (ORDER BY elo_rating DESC) as global_rank,
    RANK() OVER (PARTITION BY college_campus ORDER BY elo_rating DESC) as campus_rank,
    RANK() OVER (PARTITION BY academic_section ORDER BY elo_rating DESC) as section_rank
FROM users
WHERE elo_rating IS NOT NULL;

-- Materialized View Indexes
CREATE UNIQUE INDEX idx_leaderboard_cache_user_id ON leaderboard_cache(user_id);
CREATE INDEX idx_leaderboard_cache_global ON leaderboard_cache(global_rank);
CREATE INDEX idx_leaderboard_cache_campus ON leaderboard_cache(college_campus, campus_rank);
CREATE INDEX idx_leaderboard_cache_section ON leaderboard_cache(academic_section, section_rank);
