"""Storage Setup and Initialization

This module handles the setup and initialization of storage infrastructure, including:
- SQLite database creation and initialization
- Google Cloud Storage (GCS) bucket provisioning
- Environment configuration management
- Storage access validation

The module provides core functionality for:
- Database schema creation using SQLAlchemy models
- GCS bucket creation with versioning enabled
- Configuration file management
- Secret management integration
- Comprehensive monitoring and logging

Example:

    >>> from utils.setup_storage import setup_gcs, init_database
    >>> 
    >>> # Initialize storage infrastructure
    >>> if setup_gcs() and init_database():
    ...     print("Storage infrastructure ready")
    ... 
    >>> # Load and validate configuration
    >>> config = load_gcs_config()
    >>> if config and validate_setup():
    ...     print(f"Using GCS bucket: {config.GCS_BUCKET_NAME}")
    ...

Use this module as part of your application's initialization process to ensure
proper storage setup before core functionality becomes available.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# Create a mock Base and engine since there's no ailf.database module
Base = declarative_base()
engine = create_engine('sqlite:///memory:')

from .local import LocalStorage
from ..core.logging import setup_logging
from ..core.monitoring import setup_monitoring
from ailf.schemas.storage import StorageConfig  # Corrected import to absolute
from ..cloud.secrets import secret_manager

# Initialize core components
logger = setup_logging('setup_storage')
monitoring = setup_monitoring('storage')


def init_database() -> bool:
    """Initialize SQLite database.

    Creates all necessary database tables using SQLAlchemy models.
    Tracks the operation using monitoring.

    Returns:
        bool: True if initialization successful, False otherwise

    Example:
        ```python
        if init_database():
            logger.info("Database initialized successfully")
        ```
    """
    try:
        monitoring.increment('init_database')
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        monitoring.track_success('init_database')
        return True

    except Exception as e:
        monitoring.track_error('init_database', str(e))
        logger.error(f"Error initializing database: {str(e)}")
        return False


def load_gcs_config() -> Optional[StorageConfig]:
    """Load GCS configuration from config file.

    Reads and validates GCS configuration from the local config file.
    Tracks operation using monitoring.

    Returns:
        Optional[StorageConfig]: Configuration object or None if file doesn't exist

    Example:
        ```python
        config = load_gcs_config()
        if config:
            print(f"Using bucket: {config.GCS_BUCKET_NAME}")
        ```
    """
    try:
        monitoring.increment('load_config')
        config_path = Path(__file__).parent.parent.parent / \
            'config' / 'gcs.json'

        if not config_path.exists():
            return None

        with open(config_path) as f:
            config_data = json.load(f)
            config = StorageConfig(**config_data)

        monitoring.track_success('load_config')
        return config

    except Exception as e:
        monitoring.track_error('load_config', str(e))
        logger.error(f"Error loading GCS config: {str(e)}")
        return None


def get_repo_identifier() -> str:
    """Get a unique identifier for this repository."""
    try:
        # Try to use the git remote URL first
        import git
        try:
            repo = git.Repo(search_parent_directories=True)
            remote_url = repo.remotes.origin.url
            return remote_url.split('/')[-1].replace('.git', '')
        except (git.InvalidGitRepositoryError, AttributeError):
            pass
    except ImportError:
        pass

    # Fall back to directory name
    return Path.cwd().name


def setup_environment() -> bool:
    """Set up environment variables from config."""
    try:
        monitoring.increment('setup_env')
        config = load_gcs_config()

        if not config:
            logger.warning("No GCS config found, skipping environment setup")
            return False

        os.environ['GCS_BUCKET_NAME'] = config.GCS_BUCKET_NAME

        monitoring.track_success('setup_env')
        return True

    except Exception as e:
        monitoring.track_error('setup_env', str(e))
        logger.error(f"Error setting up environment: {str(e)}")
        return False


def setup_gcs() -> bool:
    """Initialize Google Cloud Storage bucket."""
    try:
        monitoring.increment('setup_gcs')
        config_path = Path(__file__).parent.parent.parent / \
            'config' / 'gcs.json'

        # Initialize storage client with credentials from secret manager
        gcs_credentials = secret_manager.get_secret('GCS_CREDENTIALS')
        if not gcs_credentials:
            raise ValueError("GCS credentials not found in secret manager")

        client = storage.Client.from_service_account_info(
            json.loads(gcs_credentials))

        # Generate unique but deterministic bucket name
        repo_id = get_repo_identifier()
        bucket_name = f'jobsearch-{repo_id}-{str(uuid.uuid5(uuid.NAMESPACE_DNS, repo_id))}'
        bucket_name = bucket_name.lower()  # GCS bucket names must be lowercase

        try:
            bucket = client.get_bucket(bucket_name)
            logger.info(f"Using existing bucket: {bucket_name}")
        except NotFound:
            logger.info(f"Creating new bucket: {bucket_name}")
            bucket = client.create_bucket(bucket_name)

        # Enable versioning for backup/recovery
        bucket.versioning_enabled = True
        bucket.patch()

        # Store the bucket name in the repository config
        config_path.parent.mkdir(exist_ok=True)
        config = {
            "GCS_BUCKET_NAME": bucket_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "repository": get_repo_identifier()
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        monitoring.track_success('setup_gcs')
        logger.info("GCS infrastructure setup complete")
        return True

    except Exception as e:
        monitoring.track_error('setup_gcs', str(e))
        logger.error(f"Error setting up GCS infrastructure: {str(e)}")
        return False


def validate_setup() -> bool:
    """Validate storage setup configuration."""
    try:
        monitoring.increment('validate_setup')
        config = load_gcs_config()

        if not config:
            logger.error("No GCS configuration found")
            return False

        client = storage.Client()
        try:
            bucket = client.get_bucket(config.GCS_BUCKET_NAME)
            # Try a test upload
            test_blob = bucket.blob('test.txt')
            test_blob.upload_from_string('test')
            test_blob.delete()

        except Exception as e:
            logger.error(f"Error validating bucket access: {str(e)}")
            return False

        monitoring.track_success('validate_setup')
        logger.info("Storage setup validated successfully")
        return True

    except Exception as e:
        monitoring.track_error('validate_setup', str(e))
        logger.error(f"Error validating setup: {str(e)}")
        return False


def main() -> int:
    """Main entry point."""
    try:
        # Initialize core database
        if not init_database():
            logger.error("Database initialization failed")
            return 1

        # Set up GCS infrastructure
        if not setup_gcs():
            logger.error("GCS setup failed")
            return 1

        # Set up environment
        if not setup_environment():
            logger.warning("Environment setup failed but continuing")

        # Validate setup
        if not validate_setup():
            logger.error("Setup validation failed")
            return 1

        logger.info("Storage setup complete")
        return 0

    except Exception as e:
        logger.error(f"Unexpected error in storage setup: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
