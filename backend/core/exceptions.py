"""Application-specific exceptions."""


class ConfigurationError(RuntimeError):
    """Raised when a required service configuration is unavailable."""


class DocumentProcessingError(RuntimeError):
    """Raised when an uploaded document cannot be processed."""
