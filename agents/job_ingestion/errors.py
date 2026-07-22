class CompanyNotFound(Exception):
    """Raised when a company slug isn't found on a job board (edge case:
    ingestion must fail gracefully here, not crash).
    """
