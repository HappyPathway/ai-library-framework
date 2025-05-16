"""Package initialization file for secret providers."""
from .base import BaseSecretsProvider
from .dotenv import DotEnvSecretsProvider

__all__ = ['BaseSecretsProvider', 'DotEnvSecretsProvider']

# Conditionally import providers based on available dependencies
try:
    from .google import GoogleSecretsProvider
    __all__.append('GoogleSecretsProvider')
except ImportError:
    pass

try:
    from .aws import AWSSecretsProvider
    __all__.append('AWSSecretsProvider')
except ImportError:
    pass

try:
    from .azure import AzureSecretsProvider
    __all__.append('AzureSecretsProvider')
except ImportError:
    pass

try:
    from .vault import VaultSecretsProvider
    __all__.append('VaultSecretsProvider')
except ImportError:
    pass
