"""Custom exceptions for Ledger System"""


class LedgerError(Exception):
    """Base exception for ledger operations"""
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.details = details


class AIParseError(LedgerError):
    """Raised when AI parsing fails"""
    def __init__(self, message: str, details: str = None):
        super().__init__(message, details)


class DocumentProcessError(LedgerError):
    """Raised when document processing fails"""
    def __init__(self, message: str, details: str = None):
        super().__init__(message, details)


class StockError(LedgerError):
    """Raised for stock-related errors (e.g., insufficient stock)"""
    def __init__(self, message: str, details: str = None):
        super().__init__(message, details)


class DatabaseError(LedgerError):
    """Raised for database operation errors"""
    def __init__(self, message: str, details: str = None):
        super().__init__(message, details)
