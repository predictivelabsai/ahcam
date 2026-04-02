-- Revenue forecasts table
CREATE TABLE IF NOT EXISTS ahcam.revenue_forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    territory VARCHAR(100),
    forecast_period VARCHAR(50),
    predicted_amount NUMERIC(15, 2),
    confidence_interval JSONB DEFAULT '{}',
    model_used VARCHAR(100),
    input_data JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecasts_production ON ahcam.revenue_forecasts(production_id);
