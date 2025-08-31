"""
connection.py
=============
Database connection management module.
Handles SQLite connections with proper error handling and resource management.
Supports configuration from external config module.

Author: Assistant
Date: 2024
"""

import sqlite3
import logging
from typing import Optional, Any
from contextlib import contextmanager

# Import configuration (adjust path as needed)
try:
    from config import get_config, DatabaseConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("Config module not found, using default settings")

# Configure module logger
logger = logging.getLogger(__name__)


class DBConnection:
    """
    Database connection manager with context manager support.
    Handles SQLite connections with proper error handling and resource management.
    Supports configuration from external config file.
    """

    def __init__(self, db_path: Optional[str] = None, use_config: bool = True):
        """
        Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file (overrides config if provided)
            use_config: Whether to use configuration from config module
        """
        if use_config and CONFIG_AVAILABLE and db_path is None:
            config = get_config()
            self.db_path = config.get_connection_string()
            self.timeout = config.connection_timeout
            logger.info(f"Loaded database path from config: {self.db_path}")
        else:
            self.db_path = db_path or ':memory:'
            self.timeout = 30

        self.connection: Optional[sqlite3.Connection] = None
        logger.info(f"Initialized DBConnection with database: {self.db_path}")

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection with foreign key support.

        Returns:
            SQLite connection object

        Raises:
            sqlite3.Error: If connection fails
        """
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False  # Allow multi-threaded access
            )
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self) -> None:
        """Close the database connection if it exists."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
            self.connection = None

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            SQLite connection object
        """
        conn = self.connect()
        try:
            yield conn
        finally:
            self.disconnect()

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        Automatically commits on success or rolls back on error.

        Yields:
            SQLite connection object
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            self.disconnect()

    def execute_script(self, script: str) -> bool:
        """
        Execute a SQL script (multiple statements).

        Args:
            script: SQL script containing multiple statements

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.executescript(script)
                logger.info("Script executed successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"Script execution failed: {e}")
            return False

    def __enter__(self):
        """Enter context manager."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type:
            if self.connection:
                self.connection.rollback()
        else:
            if self.connection:
                self.connection.commit()
        self.disconnect()

    def __repr__(self) -> str:
        """String representation of DBConnection."""
        return f"DBConnection(db_path='{self.db_path}', connected={self.connection is not None})"