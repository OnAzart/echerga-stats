
-- Table for countries (static reference data)
CREATE TABLE countries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Populate countries (one-time insert)
INSERT INTO countries (id, name) VALUES
    (112, 'Молдова'),
    (133, 'Польща'),
    (136, 'Румунія'),
    (149, 'Словаччина'),
    (167, 'Угорщина')
ON CONFLICT (id) DO NOTHING;

-- Table for static checkpoint information
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    tooltip TEXT,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    for_vehicle_type INTEGER NOT NULL,
    queue_flow INTEGER NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for dynamic queue measurements (time-series data)
CREATE TABLE IF NOT EXISTS queue_measurements (
    id BIGSERIAL PRIMARY KEY,
    checkpoint_id INTEGER NOT NULL REFERENCES checkpoints(id),
    is_paused BOOLEAN NOT NULL,
    cancel_after INTEGER NOT NULL,
    wait_time INTEGER NOT NULL,
    vehicle_in_active_queues_counts INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient time-based queries
CREATE INDEX IF NOT EXISTS idx_queue_measurements_checkpoint_id ON queue_measurements(checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_queue_measurements_created_at ON queue_measurements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_queue_measurements_checkpoint_measured ON queue_measurements(checkpoint_id, created_at DESC);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for checkpoints table
CREATE TRIGGER update_checkpoints_updated_at BEFORE UPDATE ON checkpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for the latest measurements
CREATE OR REPLACE VIEW latest_queue_status AS
SELECT DISTINCT ON (c.id)
    c.id,
    c.title,
    c.country_id,
    c.lng,
    c.lat,
    qm.is_paused,
    qm.wait_time,
    qm.vehicle_in_active_queues_counts,
    qm.created_at
FROM checkpoints c
LEFT JOIN queue_measurements qm ON c.id = qm.checkpoint_id
ORDER BY c.id, qm.created_at DESC;
