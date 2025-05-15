# Secret Providers

This section documents the various secret provider implementations in the AILF library.

```{toctree}
:maxdepth: 2

base
aws
azure
google
dotenv
vault
```

Secret providers offer a consistent interface for retrieving sensitive configuration across different environments.

## Key Components

- **Base Provider**: Abstract base class for all secret providers
- **Cloud Providers**: Implementations for AWS, Azure, and Google Cloud
- **Local Providers**: Local development options like dotenv
- **Vault Provider**: Integration with HashiCorp Vault
