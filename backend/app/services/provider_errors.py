class ProviderConfigurationError(RuntimeError):
    """Raised when a provider is selected but not configured correctly."""


class ProviderExecutionError(RuntimeError):
    """Raised when a provider call fails at runtime."""
