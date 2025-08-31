"""
config.py
=========
Database configuration and credentials management.
Supports multiple environments and secure credential storage.

Author: Assistant
Date: 2024
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Available environment configurations."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration data class."""
    db_type: str = "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ":memory:"
    username: Optional[str] = None
    password: Optional[str] = None
    db_path: Optional[str] = None  # For SQLite file path
    connection_timeout: int = 30
    pool_size: int = 5
    echo: bool = False  # SQL echo for debugging

    def get_connection_string(self) -> str:
        """
        Generate appropriate connection string based on database type.

        Returns:
            Connection string for the database
        """
        if self.db_type == "sqlite":
            return self.db_path or self.database
        elif self.db_type == "mysql":
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "db_path": self.db_path,
            "connection_timeout": self.connection_timeout,
            "pool_size": self.pool_size,
            "echo": self.echo
        }


class ConfigManager:
    """
    Manages database configurations for different environments.
    Supports loading from environment variables, JSON files, or .env files.
    """

    # Default configurations for different environments
    DEFAULT_CONFIGS = {
        Environment.DEVELOPMENT: DatabaseConfig(
            db_type="sqlite",
            database="student_dev.db",
            db_path="student_dev.db",
            echo=True
        ),
        Environment.TESTING: DatabaseConfig(
            db_type="sqlite",
            database=":memory:",
            db_path=":memory:",
            echo=False
        ),
        Environment.STAGING: DatabaseConfig(
            db_type="sqlite",
            database="student_staging.db",
            db_path="student_staging.db",
            echo=False
        ),
        Environment.PRODUCTION: DatabaseConfig(
            db_type="sqlite",
            database="student_production.db",
            db_path="student_production.db",
            echo=False
        )
    }

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            environment: Environment name (defaults to ENV variable or development)
        """
        self.environment = self._determine_environment(environment)
        self.config = self._load_config()
        logger.info(f"ConfigManager initialized for environment: {self.environment.value}")

    def _determine_environment(self, env: Optional[str]) -> Environment:
        """
        Determine which environment to use.

        Args:
            env: Environment name

        Returns:
            Environment enum value
        """
        if env:
            return Environment(env.lower())

        # Check environment variable
        env_var = os.getenv("APP_ENV", "development").lower()

        try:
            return Environment(env_var)
        except ValueError:
            logger.warning(f"Invalid environment '{env_var}', defaulting to development")
            return Environment.DEVELOPMENT

    def _load_config(self) -> DatabaseConfig:
        """
        Load configuration from various sources in order of precedence:
        1. Environment variables
        2. JSON config file
        3. .env file
        4. Default configuration

        Returns:
            DatabaseConfig object
        """
        config = self.DEFAULT_CONFIGS.get(self.environment, self.DEFAULT_CONFIGS[Environment.DEVELOPMENT])

        # Try loading from JSON config file
        json_config = self._load_from_json()
        if json_config:
            config = self._merge_configs(config, json_config)

        # Try loading from .env file
        env_config = self._load_from_dotenv()
        if env_config:
            config = self._merge_configs(config, env_config)

        # Override with environment variables (highest precedence)
        env_var_config = self._load_from_environment()
        if env_var_config:
            config = self._merge_configs(config, env_var_config)

        return config

    def _load_from_json(self) -> Optional[DatabaseConfig]:
        """
        Load configuration from JSON file.

        Returns:
            DatabaseConfig or None if file doesn't exist
        """
        config_file = f"config.{self.environment.value}.json"
        if not Path(config_file).exists():
            config_file = "config.json"

        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    db_config = data.get("database", {})

                    return DatabaseConfig(
                        db_type=db_config.get("type", "sqlite"),
                        host=db_config.get("host"),
                        port=db_config.get("port"),
                        database=db_config.get("database"),
                        username=db_config.get("username"),
                        password=db_config.get("password"),
                        db_path=db_config.get("db_path"),
                        connection_timeout=db_config.get("connection_timeout", 30),
                        pool_size=db_config.get("pool_size", 5),
                        echo=db_config.get("echo", False)
                    )
            except Exception as e:
                logger.error(f"Failed to load JSON config: {e}")

        return None

    def _load_from_dotenv(self) -> Optional[DatabaseConfig]:
        """
        Load configuration from .env file.

        Returns:
            DatabaseConfig or None if file doesn't exist
        """
        env_file = Path(".env")
        if not env_file.exists():
            return None

        try:
            # Simple .env parser
            env_vars = {}
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')

            return DatabaseConfig(
                db_type=env_vars.get("DB_TYPE", "sqlite"),
                host=env_vars.get("DB_HOST"),
                port=int(env_vars.get("DB_PORT")) if env_vars.get("DB_PORT") else None,
                database=env_vars.get("DB_DATABASE", "student.db"),
                username=env_vars.get("DB_USERNAME"),
                password=env_vars.get("DB_PASSWORD"),
                db_path=env_vars.get("DB_PATH"),
                connection_timeout=int(env_vars.get("DB_TIMEOUT", "30")),
                pool_size=int(env_vars.get("DB_POOL_SIZE", "5")),
                echo=env_vars.get("DB_ECHO", "false").lower() == "true"
            )
        except Exception as e:
            logger.error(f"Failed to load .env file: {e}")
            return None

    def _load_from_environment(self) -> Optional[DatabaseConfig]:
        """
        Load configuration from environment variables.

        Returns:
            DatabaseConfig with values from environment variables
        """
        db_type = os.getenv("DB_TYPE")
        if not db_type:
            return None

        return DatabaseConfig(
            db_type=db_type,
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None,
            database=os.getenv("DB_DATABASE", "student.db"),
            username=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            db_path=os.getenv("DB_PATH"),
            connection_timeout=int(os.getenv("DB_TIMEOUT", "30")),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )

    def _merge_configs(self, base: DatabaseConfig, override: DatabaseConfig) -> DatabaseConfig:
        """
        Merge two configurations, with override taking precedence.

        Args:
            base: Base configuration
            override: Configuration to override with

        Returns:
            Merged DatabaseConfig
        """
        merged = DatabaseConfig()

        # Merge each field
        for field in ['db_type', 'host', 'port', 'database', 'username',
                     'password', 'db_path', 'connection_timeout', 'pool_size', 'echo']:
            override_value = getattr(override, field, None)
            if override_value is not None:
                setattr(merged, field, override_value)
            else:
                setattr(merged, field, getattr(base, field, None))

        return merged

    def get_config(self) -> DatabaseConfig:
        """
        Get the current database configuration.

        Returns:
            DatabaseConfig object
        """
        return self.config

    def save_config_template(self, filename: str = "config.template.json"):
        """
        Save a configuration template file.

        Args:
            filename: Name of the template file
        """
        template = {
            "database": {
                "type": "sqlite",
                "host": "localhost",
                "port": 3306,
                "database": "student_db",
                "username": "your_username",
                "password": "your_password",
                "db_path": "student.db",
                "connection_timeout": 30,
                "pool_size": 5,
                "echo": False
            },
            "app": {
                "debug": False,
                "log_level": "INFO"
            }
        }

        with open(filename, 'w') as f:
            json.dump(template, f, indent=2)

        logger.info(f"Configuration template saved to {filename}")

    def __repr__(self) -> str:
        """String representation of ConfigManager."""
        return f"ConfigManager(environment={self.environment.value})"


# Singleton instance for easy access
_config_manager: Optional[ConfigManager] = None


def get_config() -> DatabaseConfig:
    """
    Get the current database configuration (singleton pattern).

    Returns:
        DatabaseConfig object
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def init_config(environment: Optional[str] = None) -> DatabaseConfig:
    """
    Initialize configuration with specific environment.

    Args:
        environment: Environment name

    Returns:
        DatabaseConfig object
    """
    global _config_manager
    _config_manager = ConfigManager(environment)
    return _config_manager.get_config()


# Example .env file content (save as .env in project root)
ENV_FILE_EXAMPLE = """
# Database Configuration
DB_TYPE=sqlite
DB_PATH=student_production.db
DB_DATABASE=student_production.db

# For MySQL/PostgreSQL
# DB_TYPE=mysql
# DB_HOST=localhost
# DB_PORT=3306
# DB_DATABASE=student_db
# DB_USERNAME=admin
# DB_PASSWORD=secure_password

# Connection Settings
DB_TIMEOUT=30
DB_POOL_SIZE=5
DB_ECHO=false

# Application Environment
APP_ENV=production
"""

# Example config.json file content
CONFIG_JSON_EXAMPLE = """
{
  "database": {
    "type": "sqlite",
    "db_path": "student.db",
    "database": "student.db",
    "connection_timeout": 30,
    "pool_size": 5,
    "echo": false
  },
  "app": {
    "debug": false,
    "log_level": "INFO"
  }
}
"""


if __name__ == "__main__":
    """Demo configuration management."""

    print("DATABASE CONFIGURATION MANAGEMENT")
    print("=" * 50)

    # Create config manager
    manager = ConfigManager("development")
    config = manager.get_config()

    print(f"\nEnvironment: {manager.environment.value}")
    print(f"Database Type: {config.db_type}")
    print(f"Database Path: {config.db_path}")
    print(f"Connection String: {config.get_connection_string()}")

    # Save template
    manager.save_config_template()
    print("\n✓ Configuration template saved to config.template.json")

    # Show example files
    print("\n" + "=" * 50)
    print("EXAMPLE .env FILE:")
    print("=" * 50)
    print(ENV_FILE_EXAMPLE)

    print("\n" + "=" * 50)
    print("EXAMPLE config.json FILE:")
    print("=" * 50)
    print(CONFIG_JSON_EXAMPLE)