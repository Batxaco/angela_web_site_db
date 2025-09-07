"""
Credentials management module for MySQL database connections.

This module handles loading and managing database credentials from various sources
including JSON files, YAML files, and environment variables with secure handling.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseCredentials:
    """Data class for database connection credentials."""

    host: str
    port: int
    database: str
    username: str
    password: str
    connection_timeout: int = 30
    ssl_disabled: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    charset: str = 'utf8mb4'
    autocommit: bool = True

    def to_mysql_config(self) -> Dict[str, Any]:
        """
        Convert credentials to mysql-connector-python configuration.

        Returns:
            Dictionary with MySQL connector configuration
        """
        config = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password,
            'connection_timeout': self.connection_timeout,
            'charset': self.charset,
            'autocommit': self.autocommit,
            'raise_on_warnings': True,
        }

        # Add SSL configuration if provided
        if not self.ssl_disabled:
            if self.ssl_ca:
                config['ssl_ca'] = self.ssl_ca
            if self.ssl_cert:
                config['ssl_cert'] = self.ssl_cert
            if self.ssl_key:
                config['ssl_key'] = self.ssl_key
        else:
            config['ssl_disabled'] = True

        return config

    def to_pymysql_config(self) -> Dict[str, Any]:
        """
        Convert credentials to PyMySQL configuration.

        Returns:
            Dictionary with PyMySQL configuration
        """
        config = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password,
            'connect_timeout': self.connection_timeout,
            'charset': self.charset,
            'autocommit': self.autocommit,
        }

        # Add SSL configuration if provided
        if not self.ssl_disabled and (self.ssl_ca or self.ssl_cert or self.ssl_key):
            ssl_config = {}
            if self.ssl_ca:
                ssl_config['ca'] = self.ssl_ca
            if self.ssl_cert:
                ssl_config['cert'] = self.ssl_cert
            if self.ssl_key:
                ssl_config['key'] = self.ssl_key
            config['ssl'] = ssl_config

        return config

    def get_display_info(self) -> Dict[str, Any]:
        """
        Get safe display information (without password).

        Returns:
            Dictionary with safe connection information
        """
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'ssl_enabled': not self.ssl_disabled,
            'charset': self.charset,
        }


class CredentialsManager:
    """Manages loading and validation of database credentials."""

    def __init__(self, credentials_file: str = 'credentials.json') -> None:
        """
        Initialize credentials manager.

        Args:
            credentials_file: Path to credentials file
        """
        self.credentials_file = credentials_file
        self._credentials: Optional[DatabaseCredentials] = None

    def load_credentials(self) -> DatabaseCredentials:
        """
        Load credentials from file or environment variables.

        Returns:
            DatabaseCredentials instance

        Raises:
            FileNotFoundError: If credentials file is not found and env vars missing
            ValueError: If required credentials are missing
        """
        # Try loading from environment variables first
        try:
            credentials = self._load_from_environment()
            if credentials:
                self._credentials = credentials
                logger.info("Credentials loaded from environment variables")
                return credentials
        except ValueError as e:
            logger.debug(f"Failed to load from environment: {e}")

        # Try loading from file
        if Path(self.credentials_file).exists():
            try:
                credentials = self._load_from_file()
                self._credentials = credentials
                logger.info(f"Credentials loaded from {self.credentials_file}")
                return credentials
            except Exception as e:
                logger.error(f"Failed to load credentials from file: {e}")
                raise

        raise FileNotFoundError(
            f"Credentials file '{self.credentials_file}' not found and "
            "required environment variables not set"
        )

    def _load_from_environment(self) -> Optional[DatabaseCredentials]:
        """
        Load credentials from environment variables.

        Returns:
            DatabaseCredentials if all required vars are present, None otherwise

        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = ['DB_HOST', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        return DatabaseCredentials(
            host=os.getenv('DB_HOST', ''),
            port=int(os.getenv('DB_PORT', '3306')),
            database=os.getenv('DB_DATABASE', ''),
            username=os.getenv('DB_USERNAME', ''),
            password=os.getenv('DB_PASSWORD', ''),
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            ssl_disabled=os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true',
            ssl_ca=os.getenv('DB_SSL_CA'),
            ssl_cert=os.getenv('DB_SSL_CERT'),
            ssl_key=os.getenv('DB_SSL_KEY'),
            charset=os.getenv('DB_CHARSET', 'utf8mb4'),
            autocommit=os.getenv('DB_AUTOCOMMIT', 'true').lower() == 'true',
        )

    def _load_from_file(self) -> DatabaseCredentials:
        """
        Load credentials from JSON or YAML file.

        Returns:
            DatabaseCredentials instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid or required fields missing
        """
        if not Path(self.credentials_file).exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")

        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                if self.credentials_file.endswith(('.yml', '.yaml')):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse credentials file: {e}")

        # Extract database configuration
        db_config = data.get('database', {})
        if not db_config:
            raise ValueError("No 'database' section found in credentials file")

        # Validate required fields
        required_fields = ['host', 'database', 'username', 'password']
        missing_fields = [field for field in required_fields if not db_config.get(field)]

        if missing_fields:
            raise ValueError(f"Missing required fields in credentials: {missing_fields}")

        return DatabaseCredentials(
            host=db_config['host'],
            port=int(db_config.get('port', 3306)),
            database=db_config['database'],
            username=db_config['username'],
            password=db_config['password'],
            connection_timeout=int(db_config.get('connection_timeout', 30)),
            ssl_disabled=db_config.get('ssl_disabled', False),
            ssl_ca=db_config.get('ssl_ca'),
            ssl_cert=db_config.get('ssl_cert'),
            ssl_key=db_config.get('ssl_key'),
            charset=db_config.get('charset', 'utf8mb4'),
            autocommit=db_config.get('autocommit', True),
        )

    def get_credentials(self) -> DatabaseCredentials:
        """
        Get cached credentials or load them if not already loaded.

        Returns:
            DatabaseCredentials instance
        """
        if self._credentials is None:
            self._credentials = self.load_credentials()
        return self._credentials

    def validate_credentials(self, credentials: DatabaseCredentials) -> bool:
        """
        Validate credentials format and required fields.

        Args:
            credentials: DatabaseCredentials to validate

        Returns:
            True if valid, False otherwise
        """
        required_attrs = ['host', 'database', 'username', 'password']

        for attr in required_attrs:
            if not getattr(credentials, attr):
                logger.error(f"Missing required credential: {attr}")
                return False

        if not isinstance(credentials.port, int) or not (1 <= credentials.port <= 65535):
            logger.error(f"Invalid port number: {credentials.port}")
            return False

        if credentials.connection_timeout <= 0:
            logger.error(f"Invalid connection timeout: {credentials.connection_timeout}")
            return False

        return True

    def update_credentials_file(self, credentials: DatabaseCredentials) -> None:
        """
        Update credentials file with new credentials.

        Args:
            credentials: New credentials to save

        Raises:
            IOError: If file cannot be written
        """
        try:
            # Load existing file or create new structure
            if Path(self.credentials_file).exists():
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    if self.credentials_file.endswith(('.yml', '.yaml')):
                        data = yaml.safe_load(f) or {}
                    else:
                        data = json.load(f)
            else:
                data = {}

            # Update database section
            data['database'] = {
                'type': 'mysql',
                'host': credentials.host,
                'port': credentials.port,
                'database': credentials.database,
                'username': credentials.username,
                'password': credentials.password,
                'connection_timeout': credentials.connection_timeout,
                'ssl_disabled': credentials.ssl_disabled,
                'charset': credentials.charset,
                'autocommit': credentials.autocommit,
            }

            # Add SSL settings if provided
            if credentials.ssl_ca:
                data['database']['ssl_ca'] = credentials.ssl_ca
            if credentials.ssl_cert:
                data['database']['ssl_cert'] = credentials.ssl_cert
            if credentials.ssl_key:
                data['database']['ssl_key'] = credentials.ssl_key

            # Write updated file
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                if self.credentials_file.endswith(('.yml', '.yaml')):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2)

            logger.info(f"Credentials updated in {self.credentials_file}")

        except Exception as e:
            raise IOError(f"Failed to update credentials file: {e}")


def get_database_credentials(credentials_file: str = 'credentials.json') -> DatabaseCredentials:
    """
    Convenience function to get database credentials.

    Args:
        credentials_file: Path to credentials file

    Returns:
        DatabaseCredentials instance
    """
    manager = CredentialsManager(credentials_file)
    return manager.load_credentials()


def create_sample_credentials_file(filename: str = 'credentials.json') -> None:
    """
    Create a sample credentials file with placeholders.

    Args:
        filename: Name of the file to create
    """
    sample_data = {
        "database": {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database": "student_database",
            "username": "db_user",
            "password": "your_secure_password",
            "connection_timeout": 30,
            "ssl_disabled": False,
            "charset": "utf8mb4",
            "autocommit": True
        }
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            if filename.endswith(('.yml', '.yaml')):
                yaml.dump(sample_data, f, default_flow_style=False)
            else:
                json.dump(sample_data, f, indent=2)

        logger.info(f"Sample credentials file created: {filename}")
        print(f"✅ Sample credentials file created: {filename}")
        print("⚠️  Please update with your actual database credentials")

    except Exception as e:
        logger.error(f"Failed to create sample credentials file: {e}")
        raise