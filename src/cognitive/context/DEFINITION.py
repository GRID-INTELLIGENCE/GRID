from enum import StrEnum


class ActivityDomain(StrEnum):
    """Domains of user activity for cognitive analysis."""

    SOFTWARE_DEVELOPMENT = "software_development"
    DATA_ANALYSIS = "data_analysis"
    GENERAL_RESEARCH = "general_research"
    CREATIVE_WRITING = "creative_writing"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    EDUCATION = "education"
