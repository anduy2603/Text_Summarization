class InputError(Exception):
    """Base class for input pipeline errors."""


class InputValidationError(InputError):
    """Raised when input fails validation (URL, file, size, etc.)."""


class InputLoadError(InputError):
    """Raised when content cannot be loaded or decoded."""
