-- Anomaly alerts table
CREATE TABLE IF NOT EXISTS ahcam.anomaly_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES ahcam.transactions(transaction_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES ahcam.users(user_id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anomalies_production ON ahcam.anomaly_alerts(production_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON ahcam.anomaly_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_resolved ON ahcam.anomaly_alerts(resolved);
