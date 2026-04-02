"""App configuration constants."""

APP_NAME = "Ashland Hill Collection Account Management"
APP_SHORT = "AHCAM"
APP_PORT = 5011
APP_VERSION = "0.1.0"

# Production statuses
PRODUCTION_STATUSES = ["development", "pre_production", "production", "post_production", "completed", "released"]

# Project types
PROJECT_TYPES = ["feature_film", "documentary", "series", "short", "animation"]

# Genres
GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "Horror", "Mystery", "Romance",
    "Sci-Fi", "Thriller", "War", "Western",
]

# Stakeholder roles
STAKEHOLDER_ROLES = [
    "producer", "financier", "sales_agent", "distributor",
    "profit_participant", "guild", "talent", "completion_guarantor",
]

# Waterfall rule types
RULE_TYPES = ["percentage", "fixed", "corridor", "residual"]

# Transaction types
TRANSACTION_TYPES = ["inflow", "outflow", "adjustment"]

# Transaction statuses
TRANSACTION_STATUSES = ["pending", "confirmed", "reversed"]

# Disbursement statuses
DISBURSEMENT_STATUSES = ["calculated", "approved", "processing", "completed", "failed"]

# Account statuses
ACCOUNT_STATUSES = ["active", "frozen", "closed"]

# Contract types
CONTRACT_TYPES = ["cama", "distribution", "sales", "finance", "interparty"]

# Alert severities
ALERT_SEVERITIES = ["low", "medium", "high", "critical"]

# Territories for sales mapping
TERRITORIES = [
    "Domestic (US/Canada)", "UK", "Germany", "France", "Italy", "Spain",
    "Scandinavia", "Benelux", "Australia/NZ", "Japan", "South Korea",
    "China", "Latin America", "Middle East", "Africa", "Eastern Europe",
    "India", "Southeast Asia", "Rest of World",
]

# Currencies
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY"]
