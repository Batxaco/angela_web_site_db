"""
Configuration module for MySQL Student Database Management System.

This module handles all configuration settings including runtime options,
operation flags, and application settings loaded from environment variables
or configuration files.
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Central configuration class for database operations and settings."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        """
        Initialize configuration from environment variables or config file.

        Args:
            config_file: Optional path to JSON/YAML configuration file
        """
        self.config_file = config_file
        self._config_data: Dict[str, Any] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file or environment variables."""
        if self.config_file and Path(self.config_file).exists():
            self._load_from_file()
        else:
            self._load_from_environment()

    def _load_from_file(self) -> None:
        """Load configuration from JSON or YAML file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                if self.config_file.endswith(('.yml', '.yaml')):
                    self._config_data = yaml.safe_load(file)
                else:
                    self._config_data = json.load(file)
            logger.info(f"Configuration loaded from {self.config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file {self.config_file}: {e}")
            self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        self._config_data = {
            'operations': {
                'create_schema': self._get_bool_env('CREATE_SCHEMA', True),
                'insert_sample_data': self._get_bool_env('INSERT_SAMPLE_DATA', False),
                'update_existing': self._get_bool_env('UPDATE_EXISTING', False),
                'drop_existing': self._get_bool_env('DROP_EXISTING', False),
            },
            'tables': {
                'selected_tables': self._get_list_env('SELECTED_TABLES', []),
                'exclude_tables': self._get_list_env('EXCLUDE_TABLES', []),
                'create_all': self._get_bool_env('CREATE_ALL_TABLES', True),
            },
            'database': {
                'connection_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
                'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
                'retry_attempts': int(os.getenv('DB_RETRY_ATTEMPTS', '3')),
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', 'mysql_database.log'),
                'format': os.getenv('LOG_FORMAT',
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'max_bytes': int(os.getenv('LOG_MAX_BYTES', '10485760')),  # 10MB
                'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            },
            'security': {
                'ssl_disabled': self._get_bool_env('SSL_DISABLED', False),
                'ssl_ca': os.getenv('SSL_CA'),
                'ssl_cert': os.getenv('SSL_CERT'),
                'ssl_key': os.getenv('SSL_KEY'),
            }
        }
        logger.info("Configuration loaded from environment variables")

    @staticmethod
    def _get_bool_env(key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    @staticmethod
    def _get_list_env(key: str, default: List[str]) -> List[str]:
        """Get list value from environment variable (comma-separated)."""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(',')]
        return default

    # Operation flags
    @property
    def create_schema(self) -> bool:
        """Whether to create database schema."""
        return self._config_data.get('operations', {}).get('create_schema', True)

    @property
    def insert_sample_data(self) -> bool:
        """Whether to insert sample data."""
        return self._config_data.get('operations', {}).get('insert_sample_data', False)

    @property
    def update_existing(self) -> bool:
        """Whether to update existing records."""
        return self._config_data.get('operations', {}).get('update_existing', False)

    @property
    def drop_existing(self) -> bool:
        """Whether to drop existing tables before creation."""
        return self._config_data.get('operations', {}).get('drop_existing', False)

    # Table selection
    @property
    def selected_tables(self) -> List[str]:
        """List of specific tables to operate on."""
        return self._config_data.get('tables', {}).get('selected_tables', [])

    @property
    def exclude_tables(self) -> List[str]:
        """List of tables to exclude from operations."""
        return self._config_data.get('tables', {}).get('exclude_tables', [])

    @property
    def create_all_tables(self) -> bool:
        """Whether to create all tables or only selected ones."""
        return self._config_data.get('tables', {}).get('create_all', True)

    # Database settings
    @property
    def connection_timeout(self) -> int:
        """Database connection timeout in seconds."""
        return self._config_data.get('database', {}).get('connection_timeout', 30)

    @property
    def pool_size(self) -> int:
        """Database connection pool size."""
        return self._config_data.get('database', {}).get('pool_size', 5)

    @property
    def max_overflow(self) -> int:
        """Maximum overflow connections in pool."""
        return self._config_data.get('database', {}).get('max_overflow', 10)

    @property
    def pool_timeout(self) -> int:
        """Pool timeout in seconds."""
        return self._config_data.get('database', {}).get('pool_timeout', 30)

    @property
    def retry_attempts(self) -> int:
        """Number of retry attempts for failed operations."""
        return self._config_data.get('database', {}).get('retry_attempts', 3)

    # Logging settings
    @property
    def log_level(self) -> str:
        """Logging level."""
        return self._config_data.get('logging', {}).get('level', 'INFO')

    @property
    def log_file(self) -> str:
        """Log file path."""
        return self._config_data.get('logging', {}).get('file', 'mysql_database.log')

    @property
    def log_format(self) -> str:
        """Log message format."""
        return self._config_data.get('logging', {}).get('format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @property
    def log_max_bytes(self) -> int:
        """Maximum log file size in bytes."""
        return self._config_data.get('logging', {}).get('max_bytes', 10485760)

    @property
    def log_backup_count(self) -> int:
        """Number of backup log files to keep."""
        return self._config_data.get('logging', {}).get('backup_count', 5)

    # Security settings
    @property
    def ssl_disabled(self) -> bool:
        """Whether SSL is disabled."""
        return self._config_data.get('security', {}).get('ssl_disabled', False)

    @property
    def ssl_ca(self) -> Optional[str]:
        """SSL CA certificate path."""
        return self._config_data.get('security', {}).get('ssl_ca')

    @property
    def ssl_cert(self) -> Optional[str]:
        """SSL certificate path."""
        return self._config_data.get('security', {}).get('ssl_cert')

    @property
    def ssl_key(self) -> Optional[str]:
        """SSL key path."""
        return self._config_data.get('security', {}).get('ssl_key')

    def get_table_list(self) -> List[str]:
        """
        Get list of tables to operate on based on configuration.

        Returns:
            List of table names to process
        """
        all_tables = [
            'Students', 'Teachers', 'Courses', 'Levels', 'EvaluationGroups',
            'EvaluationComponents', 'StudentScores', 'Grades', 'Tutorials', 'Bans'
        ]

        if not self.create_all_tables and self.selected_tables:
            tables = [t for t in self.selected_tables if t in all_tables]
        else:
            tables = all_tables

        # Remove excluded tables
        if self.exclude_tables:
            tables = [t for t in tables if t not in self.exclude_tables]

        return tables

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config_data.copy()

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"DatabaseConfig(config_file={self.config_file})"


# Global configuration instance
config = DatabaseConfig()


def setup_logging() -> None:
    """Setup logging configuration based on config settings."""
    from logging.handlers import RotatingFileHandler
    import sys

    # Create logs directory if it doesn't exist
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler with rotation and UTF-8 encoding
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
        encoding='utf-8'  # Add UTF-8 encoding for Unicode support
    )
    file_handler.setFormatter(logging.Formatter(config.log_format))

    # Console handler with UTF-8 encoding for Windows compatibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(config.log_format))

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("Logging configured successfully")


def load_config(config_file: Optional[str] = None) -> DatabaseConfig:
    """
    Load and return configuration instance.

    Args:
        config_file: Optional path to configuration file

    Returns:
        DatabaseConfig instance
    """
    global config
    config = DatabaseConfig(config_file)
    setup_logging()
    return config