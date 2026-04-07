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

# Distribution agreement statuses
AGREEMENT_STATUSES = ["pending", "active", "expired", "terminated"]

# Agreement types
AGREEMENT_TYPES = ["distribution", "sales", "co_production", "pre_sale", "output_deal"]

# Financial statuses for agreements
FINANCIAL_STATUSES = ["pending", "partial", "paid", "overdue"]

# Report types
REPORT_TYPES = ["collection_statement", "cgr_report", "receipts_report", "outstanding_report", "waterfall_position"]

# Extended territory list (granular)
TERRITORY_LIST = [
    "Domestic (US/Canada)", "UK", "Ireland",
    "Germany", "Austria", "Switzerland (German)",
    "France", "Belgium (French)", "Switzerland (French)",
    "Italy", "Spain", "Portugal",
    "Scandinavia", "Sweden", "Norway", "Denmark", "Finland", "Iceland",
    "Benelux", "Netherlands", "Belgium", "Luxembourg",
    "Australia", "New Zealand",
    "Japan", "South Korea", "China", "Hong Kong", "Taiwan",
    "India", "Pakistan", "Bangladesh",
    "Southeast Asia", "Thailand", "Philippines", "Indonesia", "Malaysia", "Singapore", "Vietnam",
    "Latin America", "Brazil", "Mexico", "Argentina", "Colombia", "Chile",
    "Middle East", "UAE", "Saudi Arabia", "Israel", "Turkey",
    "Africa", "South Africa", "Nigeria", "Kenya",
    "Eastern Europe", "Poland", "Czech Republic", "Hungary", "Romania", "Russia", "Ukraine",
    "Greece", "Cyprus",
    "Rest of World",
]
