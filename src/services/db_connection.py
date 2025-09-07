"""
Database connection service for MySQL Student Database Management System.

This module handles MySQL database connections with support for multiple
drivers, connection pooling, retry logic, and comprehensive error handling.
"""

import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass
import threading

from src.utils.credentials import DatabaseCredentials, CredentialsManager
from src.config.config import DatabaseConfig

logger = logging.getLogger(__name__)

# Try to import MySQL connectors
try:
    import mysql.connector
    from mysql.connector import pooling, Error as MySQLConnectorError

    MYSQL_CONNECTOR_AVAILABLE = True
except ImportError:
    MYSQL_CONNECTOR_AVAILABLE = False
    logger.info("mysql-connector-python not available")

try:
    import pymysql
    from pymysql import Error as PyMySQLError

    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger.info("PyMySQL not available")


@dataclass
class ConnectionInfo:
    """Information about database connection."""
    driver: str
    host: str
    port: int
    database: str
    username: str
    connected_at: Optional[str] = None
    connection_id: Optional[int] = None
    server_version: Optional[str] = None


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass


class DatabaseConnection:
    """
    Manages individual database connections with automatic retry and error handling.
    """

    def __init__(self, credentials: DatabaseCredentials, config: DatabaseConfig):
        """
        Initialize database connection manager.

        Args:
            credentials: Database credentials
            config: Database configuration
        """
        self.credentials = credentials
        self.config = config
        self.connection = None
        self.driver_type = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """
        Establish database connection with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        with self._lock:
            if self.is_connected():
                return True

            for attempt in range(self.config.retry_attempts):
                try:
                    if self._try_connection():
                        logger.info(f"Connected to MySQL database using {self.driver_type}")
                        return True
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.retry_attempts - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff

            logger.error("All connection attempts failed")
            return False

    def _try_connection(self) -> bool:
        """
        Attempt connection with available drivers.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If no drivers available or connection fails
        """
        if MYSQL_CONNECTOR_AVAILABLE:
            return self._connect_mysql_connector()
        elif PYMYSQL_AVAILABLE:
            return self._connect_pymysql()
        else:
            raise DatabaseConnectionError(
                "No MySQL drivers available. Install mysql-connector-python or PyMySQL"
            )

    def _connect_mysql_connector(self) -> bool:
        """Connect using mysql-connector-python."""
        try:
            config = self.credentials.to_mysql_config()
            self.connection = mysql.connector.connect(**config)
            self.driver_type = "mysql-connector-python"
            return True
        except MySQLConnectorError as e:
            logger.error(f"MySQL Connector connection failed: {e}")
            return False

    def _connect_pymysql(self) -> bool:
        """Connect using PyMySQL."""
        try:
            config = self.credentials.to_pymysql_config()
            self.connection = pymysql.connect(**config)
            self.driver_type = "PyMySQL"
            return True
        except PyMySQLError as e:
            logger.error(f"PyMySQL connection failed: {e}")
            return False

    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            True if connected and alive, False otherwise
        """
        if self.connection is None:
            return False

        try:
            if self.driver_type == "mysql-connector-python":
                return self.connection.is_connected()
            elif self.driver_type == "PyMySQL":
                self.connection.ping(reconnect=False)
                return True
        except Exception:
            return False

        return False

    def reconnect(self) -> bool:
        """
        Reconnect to database.

        Returns:
            True if reconnection successful
        """
        logger.info("Attempting to reconnect to database...")
        self.close()
        return self.connect()

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            if self.connection:
                try:
                    self.connection.close()
                    logger.info("Database connection closed")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
                finally:
                    self.connection = None
                    self.driver_type = None

    def get_connection_info(self) -> ConnectionInfo:
        """
        Get information about current connection.

        Returns:
            ConnectionInfo object with connection details
        """
        if not self.is_connected():
            raise DatabaseConnectionError("Not connected to database")

        try:
            cursor = self.connection.cursor()

            # Get server version
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]

            # Get connection ID
            cursor.execute("SELECT CONNECTION_ID()")
            conn_id = cursor.fetchone()[0]

            cursor.close()

            return ConnectionInfo(
                driver=self.driver_type,
                host=self.credentials.host,
                port=self.credentials.port,
                database=self.credentials.database,
                username=self.credentials.username,
                connection_id=conn_id,
                server_version=version,
                connected_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )

        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            raise DatabaseConnectionError(f"Failed to get connection info: {e}")

    @contextmanager
    def get_cursor(self, dictionary: bool = False):
        """
        Get database cursor with automatic cleanup.

        Args:
            dictionary: Whether to return results as dictionaries

        Yields:
            Database cursor

        Raises:
            DatabaseConnectionError: If not connected or cursor creation fails
        """
        if not self.is_connected():
            if not self.connect():
                raise DatabaseConnectionError("Unable to establish database connection")

        cursor = None
        try:
            if self.driver_type == "mysql-connector-python":
                cursor = self.connection.cursor(dictionary=dictionary)
            elif self.driver_type == "PyMySQL":
                if dictionary:
                    cursor = self.connection.cursor(pymysql.cursors.DictCursor)
                else:
                    cursor = self.connection.cursor()

            yield cursor

        except Exception as e:
            logger.error(f"Cursor operation failed: {e}")
            raise DatabaseConnectionError(f"Cursor operation failed: {e}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    logger.warning(f"Error closing cursor: {e}")


class ConnectionPool:
    """
    Database connection pool for managing multiple connections efficiently.
    """

    def __init__(self, credentials: DatabaseCredentials, config: DatabaseConfig):
        """
        Initialize connection pool.

        Args:
            credentials: Database credentials
            config: Database configuration
        """
        self.credentials = credentials
        self.config = config
        self._pool = None
        self._lock = threading.Lock()

    def create_pool(self) -> bool:
        """
        Create connection pool.

        Returns:
            True if pool created successfully
        """
        with self._lock:
            if self._pool is not None:
                return True

            try:
                if MYSQL_CONNECTOR_AVAILABLE:
                    return self._create_mysql_connector_pool()
                else:
                    logger.warning("Connection pooling requires mysql-connector-python")
                    return False
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                return False

    def _create_mysql_connector_pool(self) -> bool:
        """Create MySQL Connector pool."""
        try:
            config = self.credentials.to_mysql_config()
            config.update({
                'pool_name': 'student_db_pool',
                'pool_size': self.config.pool_size,
                'pool_reset_session': True,
                'autocommit': True
            })

            self._pool = mysql.connector.pooling.MySQLConnectionPool(**config)
            logger.info(f"Connection pool created with {self.config.pool_size} connections")
            return True

        except MySQLConnectorError as e:
            logger.error(f"Failed to create MySQL connection pool: {e}")
            return False

    @contextmanager
    def get_connection(self):
        """
        Get connection from pool with automatic return.

        Yields:
            Database connection

        Raises:
            DatabaseConnectionError: If pool not available or connection fails
        """
        if self._pool is None:
            if not self.create_pool():
                raise DatabaseConnectionError("Connection pool not available")

        connection = None
        try:
            connection = self._pool.get_connection()
            yield connection
        except Exception as e:
            logger.error(f"Pool connection error: {e}")
            raise DatabaseConnectionError(f"Pool connection error: {e}")
        finally:
            if connection:
                try:
                    connection.close()  # Return to pool
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")

    def close_pool(self) -> None:
        """Close all connections in pool."""
        with self._lock:
            if self._pool:
                try:
                    # MySQL Connector pools don't have explicit close method
                    # Connections will be closed when pool is garbage collected
                    self._pool = None
                    logger.info("Connection pool closed")
                except Exception as e:
                    logger.warning(f"Error closing connection pool: {e}")


class DatabaseService:
    """
    High-level database service providing connection management and common operations.
    """

    def __init__(self, credentials_file: str = 'credentials.json', config: Optional[DatabaseConfig] = None):
        """
        Initialize database service.

        Args:
            credentials_file: Path to credentials file
            config: Database configuration (optional)
        """
        self.credentials_manager = CredentialsManager(credentials_file)
        self.config = config or DatabaseConfig()
        self.credentials = None
        self.connection = None
        self.pool = None

    def initialize(self) -> bool:
        """
        Initialize database service.

        Returns:
            True if initialization successful
        """
        try:
            # Load credentials
            self.credentials = self.credentials_manager.load_credentials()

            # Create connection and pool
            self.connection = DatabaseConnection(self.credentials, self.config)
            self.pool = ConnectionPool(self.credentials, self.config)

            # Test connection
            if not self.test_connection():
                logger.error("Database connection test failed")
                return False

            logger.info("Database service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Database service initialization failed: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection test successful
        """
        try:
            if not self.connection.connect():
                return False

            with self.connection.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            logger.info("Database connection test successful")
            return result[0] == 1

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get comprehensive connection information.

        Returns:
            Dictionary with connection details
        """
        try:
            conn_info = self.connection.get_connection_info()
            return {
                'driver': conn_info.driver,
                'host': conn_info.host,
                'port': conn_info.port,
                'database': conn_info.database,
                'username': conn_info.username,
                'server_version': conn_info.server_version,
                'connection_id': conn_info.connection_id,
                'connected_at': conn_info.connected_at,
                'pool_available': self.pool._pool is not None if self.pool else False
            }
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return {'error': str(e)}

    def execute_query(self, query: str, params: Optional[Tuple] = None,
                      fetch: bool = True) -> Optional[List[Any]]:
        """
        Execute SQL query with automatic connection management.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            Query results if fetch=True, None otherwise
        """
        try:
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, params or ())

                if fetch:
                    return cursor.fetchall()
                else:
                    self.connection.connection.commit()
                    return None

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}")

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute query with multiple parameter sets.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        try:
            with self.connection.get_cursor() as cursor:
                cursor.executemany(query, params_list)
                self.connection.connection.commit()
                return cursor.rowcount

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise DatabaseConnectionError(f"Batch execution failed: {e}")

    def close(self) -> None:
        """Close all database connections."""
        if self.connection:
            self.connection.close()
        if self.pool:
            self.pool.close_pool()
        logger.info("Database service closed")


def create_database_service(credentials_file: str = 'credentials.json',
                            config: Optional[DatabaseConfig] = None) -> DatabaseService:
    """
    Factory function to create and initialize database service.

    Args:
        credentials_file: Path to credentials file
        config: Database configuration

    Returns:
        Initialized DatabaseService instance

    Raises:
        DatabaseConnectionError: If initialization fails
    """
    service = DatabaseService(credentials_file, config)

    if not service.initialize():
        raise DatabaseConnectionError("Failed to initialize database service")

    return service


def check_driver_availability() -> Dict[str, bool]:
    """
    Check availability of MySQL drivers.

    Returns:
        Dictionary with driver availability status
    """
    return {
        'mysql-connector-python': MYSQL_CONNECTOR_AVAILABLE,
        'pymysql': PYMYSQL_AVAILABLE,
        'any_available': MYSQL_CONNECTOR_AVAILABLE or PYMYSQL_AVAILABLE
    }